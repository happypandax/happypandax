import NextAuth from 'next-auth';

import { handler, nextAuthOptions } from '../../../server/requests';

export default handler().all(NextAuth(nextAuthOptions));
