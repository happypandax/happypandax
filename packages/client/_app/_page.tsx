import { redirect } from 'next/navigation';

export async function getServerSideProps(context) {
  return {
    redirect: {
      destination: '/library',
      permanent: false,
    },
    props: {},
  };
}

export default function Page({}: {
  params: { slug: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}) {
  redirect('/library');
}
