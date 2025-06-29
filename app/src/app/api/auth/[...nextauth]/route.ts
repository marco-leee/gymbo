import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";


// Create NextAuth handler
function createNextAuthHandler() {
  return NextAuth({
    providers: [
      GoogleProvider({
        clientId: process.env.GOOGLE_CLIENT_ID!,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
        httpOptions: {
          timeout: 40000,
        },
        // authorization: {
        //   params: {
        //     prompt: "consent",
        //     access_type: "offline",
        //     response_type: "code",
        //   },
        // },
      }),
    ],
    callbacks: {
      async jwt({ token, account, user, trigger, session }) {
        
        if (account) {
          try {
            // Store Google OAuth information
            token = Object.assign({}, token, {
              id_token: account.id_token,
              // Note: We'll need to determine the gateway from the callback URL
              // This will be handled in the callback page
            });
          } catch (error) {
            console.error(`Authentication error:`, error);
            throw error;
          }
        }

        // Handle session update if needed
        if (trigger === "update" && session?.gateway) {
          token.gateway = session.gateway;
          token.user_type = session.gateway;
        }

        return token;
      },
      async session({ session, token }) {
        if (session) {
          session = Object.assign({}, session, {
            id_token: token.id_token,
            authToken: token.myToken,
            gateway: token.gateway,
            user_type: token.user_type,
          });
        }
        return session;
      },
    },
    pages: {
      signIn: `/login`,
      error: `/login?error=AuthenticationError`,
    },
    // Gateway-specific session configuration
    session: {
      strategy: "jwt",
      maxAge: 24 * 60 * 60, // 24 hours
    },
    // Add gateway to the session for debugging/logging
    debug: process.env.NODE_ENV === "development",
  });
}

const nextAuthHandler = createNextAuthHandler()

export { nextAuthHandler as GET, nextAuthHandler as POST }; 