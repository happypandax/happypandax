import { redirect } from 'next/navigation';

import { ServiceType } from '../../server/constants';
import LoginSegment from './segment';

export default function Page({
  searchParams,
}: {
  params: { slug: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}) {
  const server = global.app.service.get(ServiceType.Server);
  const next = searchParams?.next
    ? decodeURIComponent(searchParams?.next as string)
    : undefined;

  if (server.logged_in) {
    redirect(next ?? '/library');
  }

  return <LoginSegment next={next} />;
}
