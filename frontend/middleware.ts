import { NextResponse, type NextRequest } from "next/server";

// Pass-through middleware. Auth gating is handled client-side in each page via
// supabase.auth.getSession(), so the edge middleware does not need to call
// Supabase. A network call here (auth.getUser) is fragile on Vercel's Edge
// runtime and was crashing every request with MIDDLEWARE_INVOCATION_FAILED.
export function middleware(_req: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
