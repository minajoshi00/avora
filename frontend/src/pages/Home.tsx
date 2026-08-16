import { Hero } from '../components/Hero';
import { FirstContact } from '../components/sections/FirstContact';
import { NotAChatbot } from '../components/sections/NotAChatbot';
import { ExperienceSection } from '../components/sections/Experience';
import { Ecosystem } from '../components/sections/Ecosystem';
import { IntelligenceSystem } from '../components/sections/IntelligenceSystem';
import { ModesExperience } from '../components/sections/ModesExperience';
import { DownloadCenter } from '../components/sections/DownloadCenter';
import { Vision } from '../components/sections/Vision';
import { CTA } from '../components/CTA';
import { ScrollReveal } from '../components/sections/ScrollReveal';
import { ChatPreview } from '../components/sections/ChatPreview';
import { CreatorStory } from '../components/sections/CreatorStory';

export function Home() {
  return (
    <main className="min-h-screen">
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

      {/* What AVORA does */}
      <ScrollReveal direction="up" duration={0.8} delay={0.25}>
        <ExperienceSection />
</ScrollReveal>

      <ScrollReveal direction="up" duration={0.8} delay={0.3}>
        <Ecosystem />
        <IntelligenceSystem />
        <ModesExperience />
        <CreatorStory />
</ScrollReveal>

      <ScrollReveal direction="up" duration={0.8} delay={0.4}>
        <Vision />
</ScrollReveal>

      <ScrollReveal direction="up" duration={0.8} delay={0.5}>
        <DownloadCenter />
</ScrollReveal>

      <ScrollReveal direction="up" duration={0.8} delay={0.55}>
        <CTA />
</ScrollReveal>
    </main>
  );
}