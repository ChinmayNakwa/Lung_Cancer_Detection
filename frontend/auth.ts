import NextAuth, { CredentialsSignin } from "next-auth";
import Credentials from "next-auth/providers/credentials";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// Lets the login page tell a lockout apart from a wrong password
class RateLimited extends CredentialsSignin {
  code = "rate_limited";
}

declare module "next-auth" {
  interface User {
    accessToken?: string;
    accessTokenExpires?: number; // epoch milliseconds
  }
  interface Session {
    accessToken?: string;
    accessTokenExpires?: number;
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        // The backend owns the admin account and issues the API token
        const res = await fetch(`${API_URL}/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: credentials.username,
            password: credentials.password,
          }),
        });
        if (res.status === 429) throw new RateLimited();
        if (!res.ok) return null;

        const data = await res.json();
        return {
          id: data.username,
          name: data.username,
          accessToken: data.access_token,
          accessTokenExpires: data.expires_at * 1000,
        };
      },
    }),
  ],
  pages: {
    signIn: "/login", // We will create this custom page
  },
  callbacks: {
    jwt({ token, user }) {
      if (user?.accessToken) {
        token.accessToken = user.accessToken;
        token.accessTokenExpires = user.accessTokenExpires;
      }
      return token;
    },
    session({ session, token }) {
      session.accessToken = token.accessToken as string | undefined;
      session.accessTokenExpires = token.accessTokenExpires as number | undefined;
      return session;
    },
    authorized({ auth, request: { nextUrl } }) {
      // NextAuth keeps extending its own session, so also require the
      // backend token to be unexpired or admin calls would all get 401
      const isLoggedIn =
        !!auth?.user &&
        !!auth.accessTokenExpires &&
        Date.now() < auth.accessTokenExpires;
      const isOnProtected = nextUrl.pathname.startsWith('/admin') || nextUrl.pathname.startsWith('/validate');

      if (isOnProtected) {
        if (isLoggedIn) return true;
        return false; // Redirect to login
      }
      return true;
    },
  },
});
