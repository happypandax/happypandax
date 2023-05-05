import NextAuth from 'next-auth';

import { handler, nextAuthOptions } from '../../../server/requests';

export default handler({ auth: false }).all(NextAuth(nextAuthOptions));
