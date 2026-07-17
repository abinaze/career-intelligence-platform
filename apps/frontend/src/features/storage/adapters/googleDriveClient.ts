import type { GoogleDriveFileContents } from "../types";

/**
 * Raw Google Drive REST client.
 *
 * Called directly from the browser with the user's own Drive access
 * token — never routed through our backend. This is the whole point of
 * the BYOS Google Drive design: once GoogleDriveOAuthService hands the
 * browser its tokens, the backend is out of the loop entirely (see
 * docs/architecture/byos.md).
 *
 * Deliberately dependency-free (plain fetch), matching this project's
 * existing norm of not adding a package (e.g. googleapis) for what's a
 * small, fixed set of REST calls against a single well-known file.
 *
 * Every method here takes a raw access token as an argument rather than
 * reading it from storage — token lifecycle (refresh, expiry) is
 * GoogleDriveAdapter's job, not this module's. This keeps the client a
 * pure, stateless wrapper around Drive's API.
 */

const DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files";
const DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files";
const DATA_FILE_NAME = "career-intelligence-data.json";

export class GoogleDriveApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "GoogleDriveApiError";
  }
}

function authHeaders(accessToken: string): HeadersInit {
  return { Authorization: `Bearer ${accessToken}` };
}

async function assertOk(response: Response, action: string): Promise<void> {
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new GoogleDriveApiError(
      `Google Drive ${action} failed (${response.status}): ${body.slice(0, 300)}`,
      response.status,
    );
  }
}

export const googleDriveClient = {
  /**
   * Finds the app's data file inside the hidden appDataFolder space.
   * Returns its file ID, or null if it doesn't exist yet (first save).
   */
  async findDataFile(accessToken: string): Promise<string | null> {
    const params = new URLSearchParams({
      spaces: "appDataFolder",
      q: `name = '${DATA_FILE_NAME}' and trashed = false`,
      fields: "files(id, name)",
      pageSize: "1",
    });
    const response = await fetch(`${DRIVE_FILES_URL}?${params.toString()}`, {
      headers: authHeaders(accessToken),
    });
    await assertOk(response, "file search");

    const data = (await response.json()) as { files: Array<{ id: string }> };
    return data.files[0]?.id ?? null;
  },

  /** Reads and parses the data file's contents. */
  async readDataFile(accessToken: string, fileId: string): Promise<GoogleDriveFileContents> {
    const response = await fetch(`${DRIVE_FILES_URL}/${fileId}?alt=media`, {
      headers: authHeaders(accessToken),
    });
    await assertOk(response, "file read");
    return (await response.json()) as GoogleDriveFileContents;
  },

  /**
   * Creates or updates the data file. Pass `fileId` when one is already
   * known (from findDataFile) to update it in place; pass null to create
   * it for the first time. Returns the file's ID either way.
   */
  async writeDataFile(
    accessToken: string,
    fileId: string | null,
    contents: GoogleDriveFileContents,
  ): Promise<string> {
    const body = JSON.stringify(contents);

    if (fileId) {
      const response = await fetch(`${DRIVE_UPLOAD_URL}/${fileId}?uploadType=media`, {
        method: "PATCH",
        headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
        body,
      });
      await assertOk(response, "file update");
      return fileId;
    }

    const boundary = "cip_drive_boundary";
    const metadata = JSON.stringify({ name: DATA_FILE_NAME, parents: ["appDataFolder"] });
    const multipartBody =
      `--${boundary}\r\n` +
      `Content-Type: application/json; charset=UTF-8\r\n\r\n${metadata}\r\n` +
      `--${boundary}\r\n` +
      `Content-Type: application/json\r\n\r\n${body}\r\n` +
      `--${boundary}--`;

    const response = await fetch(`${DRIVE_UPLOAD_URL}?uploadType=multipart`, {
      method: "POST",
      headers: {
        ...authHeaders(accessToken),
        "Content-Type": `multipart/related; boundary=${boundary}`,
      },
      body: multipartBody,
    });
    await assertOk(response, "file create");

    const created = (await response.json()) as { id: string };
    return created.id;
  },

  /** Permanently deletes the data file. Used by GoogleDriveAdapter.clearAll(). */
  async deleteDataFile(accessToken: string, fileId: string): Promise<void> {
    const response = await fetch(`${DRIVE_FILES_URL}/${fileId}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
    });
    // A 404 here means it's already gone — treat that as success too.
    if (response.status !== 404) {
      await assertOk(response, "file delete");
    }
  },
};
