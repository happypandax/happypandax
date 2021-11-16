import { useRouter } from 'next/router';

import DirectoryPage from './';

interface PageProps {}

export async function getServerSideProps(context) {
  return {
    props: {},
  };
}
export default function Page({}: PageProps) {
  const router = useRouter();

  return <DirectoryPage>filter</DirectoryPage>;
}
