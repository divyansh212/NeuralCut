import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

// The skill's most common first-deploy crash: middleware calls Supabase with
// non-null assertions, so a missing env var 500s EVERY request at the edge.
// Guard it — fail open to a working page instead of a 500.
export async function middleware(req: NextRequest) {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anon) return NextResponse.next();

  const res = NextResponse.next();
  const supabase = createServerClient(url, anon, {
    cookies: {
      getAll: () => req.cookies.getAll(),
      setAll: (cookies: { name: string; value: string; options?: any }[]) =>
        cookies.forEach(({ name, value, options }) => res.cookies.set(name, value, options)),
    },
  });
  await supabase.auth.getUser(); // refresh session
  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
