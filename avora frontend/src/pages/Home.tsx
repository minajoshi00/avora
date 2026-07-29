import { Hero } from '../components/Hero';
import { FirstContact } from '../components/sections/FirstContact';
import { CapabilityExplorer } from '../components/capabilities/CapabilityExplorer';
import { ExperienceSection } from '../components/sections/Experience';
import { ProductExperience } from '../components/sections/ProductExperience';
import { Vision } from '../components/sections/Vision';
import { CreatorStory } from '../components/sections/CreatorStory';
import { CTA } from '../components/CTA';
import { ScrollReveal } from '../components/sections/ScrollReveal';
import { ChatPreview } from '../components/sections/ChatPreview';
import { IntelligenceSystem } from '../components/sections/IntelligenceSystem';
import { InteractiveDemo } from '../components/sections/InteractiveDemo';
import { DownloadCenter } from '../components/sections/DownloadCenter';
import { Ecosystem } from '../components/sections/Ecosystem';
import { ModesExperience } from '../components/sections/ModesExperience';
import { PrivacySection } from '../components/sections/PrivacySection';
import { FutureRoadmap } from '../components/sections/FutureRoadmap';
import { NotAChatbot } from '../components/sections/NotAChatbot';
import { CompanionExperience } from '../components/sections/CompanionExperience';
import { InternalWorld } from '../components/sections/InternalWorld';

export function Home() {
  return (
    <main>
      <Hero />
      
      {/* AI Chat Preview Widget */}
      <ScrollReveal direction="up" duration={1}>
        <ChatPreview />
      </ScrollReveal>

      <ScrollReveal direction="up" duration={0.8} delay={0.1}>
        <FirstContact />
      </ScrollReveal>
      
      {/* Not a Chatbot - The difference */}
      <ScrollReveal direction="up" duration={0.8} delay={0.15}>
        <NotAChatbot />
      </ScrollReveal>
      
      {/* The Companion - AVORA is already there */}
      <ScrollReveal direction="up" duration={0.8} delay={0.25}>
        <CompanionExperience />
      </ScrollReveal>
      
      {/* Inside AVORA - The intelligence within */}
      <ScrollReveal direction="up" duration={0.8} delay={0.3}>
        <InternalWorld />
      </ScrollReveal>
      
      {/* Intelligence System - How AVORA thinks */}
      <ScrollReveal direction="up" duration={0.8} delay={0.35}>
        <IntelligenceSystem />
      </ScrollReveal>
      
      <ScrollReveal direction="up" duration={0.8} delay={0.4}>
        <CapabilityExplorer />
      </ScrollReveal>
      
      <ScrollReveal direction="up" duration={0.8} delay={0.25}>
        <ExperienceSection />
      </ScrollReveal>
      
      {/* Ecosystem */}
      <ScrollReveal direction="up" duration={0.8} delay={0.3}>
        <Ecosystem />
      </ScrollReveal>
      
      {/* Modes Experience */}
      <ScrollReveal direction="up" duration={0.8} delay={0.35}>
        <ModesExperience />
      </ScrollReveal>
      
      <ScrollReveal direction="up" duration={0.8} delay={0.4}>
        <ProductExperience />
      </ScrollReveal>
      
      {/* Interactive Demo */}
      <ScrollReveal direction="up" duration={0.8} delay={0.45}>
        <InteractiveDemo />
      </ScrollReveal>
      
      {/* Download Center */}
      <ScrollReveal direction="up" duration={0.8} delay={0.5}>
        <DownloadCenter />
      </ScrollReveal>
      
      <ScrollReveal direction="up" duration={0.8} delay={0.55}>
        <Vision />
      </ScrollReveal>
      
      {/* Privacy Section */}
      <ScrollReveal direction="up" duration={0.8} delay={0.6}>
        <PrivacySection />
      </ScrollReveal>
      
      {/* Future Roadmap */}
      <ScrollReveal direction="up" duration={0.8} delay={0.65}>
        <FutureRoadmap />
      </ScrollReveal>
      
      <ScrollReveal direction="up" duration={0.8} delay={0.7}>
        <CreatorStory />
      </ScrollReveal>
      
      <ScrollReveal direction="up" duration={0.8} delay={0.75}>
        <CTA />
      </ScrollReveal>
    </main>
  );
}