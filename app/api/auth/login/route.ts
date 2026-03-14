import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  AUTH_COOKIE_NAME,
  SESSION_TTL_SECONDS,
  createSessionToken,
  isValidLogin,
} from "@/lib/auth";

interface LoginBody {
  username?: string;
  password?: string;
}

export async function POST(request: Request) {
  const body = (await request.json()) as LoginBody;
  const username = body.username?.trim() || "";
  const password = body.password || "";

  if (!isValidLogin(username, password)) {
    return NextResponse.json({ success: false, message: "Invalid credentials" }, { status: 401 });
  }

  const token = await createSessionToken(username);
  const cookieStore = await cookies();

  cookieStore.set(AUTH_COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  });

  return NextResponse.json({ success: true });
}
