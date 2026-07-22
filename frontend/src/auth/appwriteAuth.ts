import { Account, Client, ID } from "appwrite";

// Used only for login/logout/registration/JWT minting — all actual data (applications, CVs)
// still goes through our own FastAPI backend, not Appwrite. Both values are public/non-secret.
const client = new Client()
  .setEndpoint(import.meta.env.VITE_APPWRITE_ENDPOINT)
  .setProject(import.meta.env.VITE_APPWRITE_PROJECT_ID);

export const account = new Account(client);
export { ID };
