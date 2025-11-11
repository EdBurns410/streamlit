import type { AppProps } from 'next/app';
import { AuthProvider } from '../components/AuthContext';
import '../styles/globals.css';

export default function SheetifyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}
