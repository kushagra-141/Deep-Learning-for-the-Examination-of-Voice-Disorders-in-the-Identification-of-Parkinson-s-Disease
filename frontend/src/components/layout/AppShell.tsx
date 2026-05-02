import { Outlet } from "react-router-dom";
import { TopNav } from "./TopNav";
import { Footer } from "./Footer";
import { DisclaimerBanner } from "../disclaimer/DisclaimerBanner";
import { HelpBot } from "../llm/HelpBot";

export function AppShell() {
  return (
    <div className="min-h-screen flex flex-col bg-background font-sans antialiased text-foreground">
      <DisclaimerBanner />
      <TopNav />
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
      <Footer />
      <HelpBot />
    </div>
  );
}
