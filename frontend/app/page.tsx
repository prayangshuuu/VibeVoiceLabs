import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { FeatureGrid } from "@/components/FeatureGrid";
import { DemoSection } from "@/components/DemoSection";
import { Footer } from "@/components/Footer";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-[#030303] bg-grid">
      <Navbar />
      <main>
        <Hero />
        <FeatureGrid />
        <DemoSection />
      </main>
      <Footer />
    </div>
  );
}
