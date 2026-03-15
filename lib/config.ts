// API Configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error(
    "CRITICAL: NEXT_PUBLIC_API_URL environment variable not set. " +
    "Frontend cannot communicate with backend. Please configure .env file."
  );
}

export { API_URL }
