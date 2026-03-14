const encoder = new TextEncoder();
const decoder = new TextDecoder();

export const AUTH_COOKIE_NAME = "lead_engine_session";
export const SESSION_TTL_SECONDS = 60 * 60 * 24 * 7;

interface SessionPayload {
  sub: string;
  iat: number;
  exp: number;
}

function getAuthSecret(): string {
  return process.env.APP_LOGIN_SECRET || "change-me-in-production";
}

export function getConfiguredUsername(): string {
  return process.env.APP_LOGIN_USERNAME || "admin";
}

export function getConfiguredPassword(): string {
  return process.env.APP_LOGIN_PASSWORD || "admin123";
}

function bytesToBase64(bytes: Uint8Array): string {
  if (typeof btoa === "function") {
    let binary = "";
    for (const byte of bytes) {
      binary += String.fromCharCode(byte);
    }
    return btoa(binary);
  }
  return Buffer.from(bytes).toString("base64");
}

function base64ToBytes(base64: string): Uint8Array {
  if (typeof atob === "function") {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }
  return Uint8Array.from(Buffer.from(base64, "base64"));
}

function toBase64Url(bytes: Uint8Array): string {
  return bytesToBase64(bytes)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function fromBase64Url(base64Url: string): Uint8Array {
  let base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
  const mod = base64.length % 4;
  if (mod > 0) {
    base64 += "=".repeat(4 - mod);
  }
  return base64ToBytes(base64);
}

async function sign(value: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(value));
  return toBase64Url(new Uint8Array(signature));
}

export async function createSessionToken(username: string): Promise<string> {
  const now = Date.now();
  const payload: SessionPayload = {
    sub: username,
    iat: now,
    exp: now + SESSION_TTL_SECONDS * 1000,
  };

  const encodedPayload = toBase64Url(encoder.encode(JSON.stringify(payload)));
  const signature = await sign(encodedPayload, getAuthSecret());
  return `${encodedPayload}.${signature}`;
}

export async function verifySessionToken(token: string): Promise<boolean> {
  const [encodedPayload, providedSignature] = token.split(".");
  if (!encodedPayload || !providedSignature) {
    return false;
  }

  const expectedSignature = await sign(encodedPayload, getAuthSecret());
  if (providedSignature !== expectedSignature) {
    return false;
  }

  try {
    const payloadText = decoder.decode(fromBase64Url(encodedPayload));
    const payload = JSON.parse(payloadText) as SessionPayload;
    return typeof payload.exp === "number" && payload.exp > Date.now();
  } catch {
    return false;
  }
}

export function isValidLogin(username: string, password: string): boolean {
  return username === getConfiguredUsername() && password === getConfiguredPassword();
}
