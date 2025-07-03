import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        // In a real app, fetch(`${API_URL}/login`) here.
        // For now, we mock the check:
        const user = { 
            id: "1", 
            name: "Dr. Rizzoli", 
            email: "admin@lungscan.ai" 
        };

        if (credentials.username === "admin" && credentials.password === "medical123") {
          return user;
        }
        return null;
      },
    }),
  ],
  pages: {
    signIn: "/login", // We will create this custom page
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isOnProtected = nextUrl.pathname.startsWith('/admin') || nextUrl.pathname.startsWith('/validate');

      if (isOnProtected) {
        if (isLoggedIn) return true;
        return false; // Redirect to login
      }
      return true;
    },
  },
});