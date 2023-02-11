import {
    AuthWrongCredentialsError,
    ConnectionError,
    ServerError,
} from 'happypandax-client';
import NextAuth, { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';

import { handler } from '../../../server/requests';
import {
    HPX_SECRET,
    LOGIN_ERROR,
    ServiceType,
} from '../../../services/constants';

export const authOptions: NextAuthOptions = {
    secret: HPX_SECRET,
    // Configure one or more authentication providers
    logger: {
        error(code, metadata) {
            global.app.log.e(code, metadata)
        },
        warn(code) {
            global.app.log.w(code)
        },
        debug(code, metadata) {
            global.app.log.d(code, metadata)
        }
    },
    providers: [
        CredentialsProvider({
            // The name to display on the sign in form (e.g. 'Sign in with...')
            name: 'Happy Panda X',
            id: "happypandax",
            type: "credentials",
            // The credentials is used to generate a suitable form on the sign in page.
            // You can specify whatever fields you are expecting to be submitted.
            // e.g. domain, username, password, 2FA token, etc.
            // You can pass any HTML attribute to the <input> tag through the object.
            credentials: {
                username: { label: "username", type: "text" },
                password: { label: "password", type: "password" },
                host: { label: "host", type: "text" },
                port: { label: "port", type: "text" }
            },
            async authorize(credentials, req) {
                // You need to provide your own logic here that takes the credentials
                // submitted and returns either a object representing a user or value
                // that is false/null if the credentials are invalid.
                // e.g. return { id: 1, name: 'J Smith', email: 'jsmith@example.com' }
                // You can also use the `req` object to obtain additional parameters
                // (i.e., the request IP address)

                const server = global.app.service.get(ServiceType.Server);
                const r = await server.login(credentials?.username, credentials?.password, {
                    host: credentials?.host,
                    port: credentials?.port ? parseInt(credentials?.port) : undefined
                }).catch((e: ServerError) => {
                    console.error(e)
                    if (e instanceof AuthWrongCredentialsError) {
                        throw new Error(LOGIN_ERROR.InvalidCredentials)
                    } else if (e instanceof ConnectionError) {
                        throw new Error(LOGIN_ERROR.ServerNotConnected)
                    } else {
                        throw new Error(e?.message)
                    }
                })

                if (!r) {
                    throw new Error(LOGIN_ERROR.InvalidCredentials)
                }

                return {
                    id: server.client.session,
                }
            }
        })
    ],
    session: {
        strategy: 'jwt',
        maxAge: 30 * 24 * 60 * 60, // 30 days,
        generateSessionToken() {
            const server = global.app.service.get(ServiceType.Server);
            return server.client.session;
        }
    },
    pages: {
        signIn: '/login',
        signOut: '/signout',
        error: '/error', // Error code passed in query string as ?error=
        verifyRequest: '',
        newUser: ''
    },
    callbacks: {
        async signIn({ user, account, profile, email, credentials }) {
            return true
        },
        async redirect({ url, baseUrl }) {
            return baseUrl
        },
        async session({ session, token, user }) {
            return session
        },
        async jwt({ token, user, account, profile, isNewUser }) {
            return token
        }
    }
}

export default handler().all(NextAuth(authOptions))