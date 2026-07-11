import "./globals.css";
import AppContent from "./AppContent";
import { AuthProvider } from "../context/AuthContext";
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata = {
  title: "a2sporttrackers",
  description: "Dashboard de Inteligência +EV",
  icons: {
    apple: "/icon-512.png",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR" className={inter.variable}>
      <body className={inter.className}>
        <AuthProvider>
          <AppContent>{children}</AppContent>
        </AuthProvider>
      </body>
    </html>
  );
}
