export async function getServerSideProps(context) {
  return {
    redirect: {
      destination: '/library',
      permanent: false,
    },
    props: {},
  };
}

export default function Page() {
  return <div>Redirecting...</div>;
}
