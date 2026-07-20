import type { DropboxFileContents } from "../types";

/**
 * Raw Dropbox API v2 REST client. Called directly from the browser with
 * the user's own Dropbox access token — never routed through our
 * backend, same BYOS design as googleDriveClient.ts/oneDriveClient.ts.
 *
 * Dropbox's API shape is genuinely different from Google's and
 * Microsoft's, not just a different base URL:
 * - Metadata-only calls (get_metadata, delete_v2) go to api.dropboxapi.com
 *   as POST requests with a JSON body.
 * - Content calls (upload, download) go to a *separate* domain,
 *   content.dropboxapi.com, and take their arguments via a
 *   `Dropbox-API-Arg` JSON header rather than the request body — the
 *   body itself is the raw file bytes.
 *
 * Because this app's Dropbox app is registered with "App folder" access
 * (configured once in the Dropbox App Console, not requested via OAuth
 * scope), paths are automatically sandboxed to the app's own folder —
 * "/career-intelligence-data.json" here never touches the user's real
 * Dropbox root.
 */

const DROPBOX_API_BASE = "https://api.dropboxapi.com/2";
const DROPBOX_CONTENT_BASE = "https://content.dropboxapi.com/2";
const DATA_FILE_PATH = "/career-intelligence-data.json";

export class DropboxApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "DropboxApiError";
  }
}

function authHeaders(accessToken: string): HeadersInit {
  return { Authorization: `Bearer ${accessToken}` };
}

async function assertOk(response: Response, action: string): Promise<void> {
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new DropboxApiError(
      `Dropbox ${action} failed (${response.status}): ${body.slice(0, 300)}`,
      response.status,
    );
  }
}

export const dropboxClient = {
  /** Whether the data file exists yet (false on first save). */
  async fileExists(accessToken: string): Promise<boolean> {
    const response = await fetch(`${DROPBOX_API_BASE}/files/get_metadata`, {
      method: "POST",
      headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
      body: JSON.stringify({ path: DATA_FILE_PATH }),
    });
    // Dropbox returns 409 with a path/not_found error tag when the file
    // doesn't exist — that's an expected "no" here, not a real error.
    if (response.status === 409) return false;
    await assertOk(response, "file lookup");
    return true;
  },

  /** Reads and parses the data file's contents. */
  async readDataFile(accessToken: string): Promise<DropboxFileContents> {
    const response = await fetch(`${DROPBOX_CONTENT_BASE}/files/download`, {
      method: "POST",
      headers: {
        ...authHeaders(accessToken),
        "Dropbox-API-Arg": JSON.stringify({ path: DATA_FILE_PATH }),
      },
    });
    await assertOk(response, "file read");
    return (await response.json()) as DropboxFileContents;
  },

  /** Creates or overwrites the data file. */
  async writeDataFile(accessToken: string, contents: DropboxFileContents): Promise<void> {
    const response = await fetch(`${DROPBOX_CONTENT_BASE}/files/upload`, {
      method: "POST",
      headers: {
        ...authHeaders(accessToken),
        "Dropbox-API-Arg": JSON.stringify({ path: DATA_FILE_PATH, mode: "overwrite" }),
        "Content-Type": "application/octet-stream",
      },
      body: JSON.stringify(contents),
    });
    await assertOk(response, "file write");
  },

  /** Permanently deletes the data file. Used by DropboxAdapter.clearAll(). */
  async deleteDataFile(accessToken: string): Promise<void> {
    const response = await fetch(`${DROPBOX_API_BASE}/files/delete_v2`, {
      method: "POST",
      headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
      body: JSON.stringify({ path: DATA_FILE_PATH }),
    });
    // 409 here means it's already gone (path/not_found) — treat as success too.
    if (response.status !== 409) {
      await assertOk(response, "file delete");
    }
  },
};
