import type { OneDriveFileContents } from "../types";

/**
 * Raw Microsoft Graph REST client, scoped to the OneDrive app folder
 * (`special/approot`) — the Graph equivalent of Google Drive's
 * appDataFolder. Called directly from the browser with the user's own
 * Graph access token, never routed through our backend — same BYOS
 * design as googleDriveClient.ts.
 *
 * Simpler than the Google Drive client: Graph supports addressing a
 * file directly by path within approot (`approot:/{filename}`), so there's
 * no separate "search for the file's ID first" step or multipart
 * create-vs-update branching — a PUT to the content endpoint creates the
 * file if it doesn't exist yet, or overwrites it if it does. This is a
 * real difference in Graph's API shape, not an oversimplification.
 */

const GRAPH_BASE = "https://graph.microsoft.com/v1.0";
const DATA_FILE_NAME = "career-intelligence-data.json";
const DATA_FILE_PATH = `${GRAPH_BASE}/me/drive/special/approot:/${DATA_FILE_NAME}`;

export class OneDriveApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "OneDriveApiError";
  }
}

function authHeaders(accessToken: string): HeadersInit {
  return { Authorization: `Bearer ${accessToken}` };
}

async function assertOk(response: Response, action: string): Promise<void> {
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new OneDriveApiError(
      `OneDrive ${action} failed (${response.status}): ${body.slice(0, 300)}`,
      response.status,
    );
  }
}

export const oneDriveClient = {
  /** Whether the data file exists yet (false on first save). */
  async fileExists(accessToken: string): Promise<boolean> {
    const response = await fetch(DATA_FILE_PATH, { headers: authHeaders(accessToken) });
    if (response.status === 404) return false;
    await assertOk(response, "file lookup");
    return true;
  },

  /** Reads and parses the data file's contents. */
  async readDataFile(accessToken: string): Promise<OneDriveFileContents> {
    const response = await fetch(`${DATA_FILE_PATH}:/content`, {
      headers: authHeaders(accessToken),
    });
    await assertOk(response, "file read");
    return (await response.json()) as OneDriveFileContents;
  },

  /** Creates or overwrites the data file — Graph handles both via the same PUT. */
  async writeDataFile(accessToken: string, contents: OneDriveFileContents): Promise<void> {
    const response = await fetch(`${DATA_FILE_PATH}:/content`, {
      method: "PUT",
      headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
      body: JSON.stringify(contents),
    });
    await assertOk(response, "file write");
  },

  /** Permanently deletes the data file. Used by OneDriveAdapter.clearAll(). */
  async deleteDataFile(accessToken: string): Promise<void> {
    const response = await fetch(DATA_FILE_PATH, {
      method: "DELETE",
      headers: authHeaders(accessToken),
    });
    if (response.status !== 404) {
      await assertOk(response, "file delete");
    }
  },
};
