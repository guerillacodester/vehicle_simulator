import "./globals.css";
import { Orbitron, Inter } from "next/font/google";
import { TransitContextProvider } from "../lib/TransitContextClient";

const orbitron = Orbitron({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-orbitron",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata = {
  title: "Arknet Transit",
  description: "Building the Backbone of Cashless Transit",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${orbitron.variable} ${inter.variable} bg-black text-white`}>
        <TransitContextProvider>
          {children}
        </TransitContextProvider>
      </body>
    </html>
  );
}
