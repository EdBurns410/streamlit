import Head from 'next/head';
import { useRouter } from 'next/router';
import { AuthForms } from '../components/AuthForms';
import { CreateToolForm } from '../components/CreateToolForm';

export default function HomePage() {
  const router = useRouter();
  return (
    <>
      <Head>
        <title>Sheetify Studio</title>
      </Head>
      <main className="min-h-screen px-6 py-12">
        <div className="mx-auto flex max-w-6xl flex-col gap-12">
          <header className="text-center">
            <h1 className="text-4xl font-bold text-white sm:text-5xl">Sheetify Studio</h1>
            <p className="mt-3 text-lg text-slate-300">
              Deploy and share Streamlit apps in a multi-tenant sandbox with one click.
            </p>
          </header>
          <div className="flex flex-col items-center gap-8 md:flex-row md:items-start">
            <AuthForms />
            <div className="flex-1">
              <CreateToolForm
                onCreated={(toolId) => {
                  router.push(`/tools/${toolId}`);
                }}
              />
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
