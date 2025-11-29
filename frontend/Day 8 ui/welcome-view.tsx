// frontend/components/app/welcome-view.tsx

import { Button } from '@/components/livekit/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText, 
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    // ----------------------------------------------------
    // 🎯 MAIN CONTAINER: Using the Renamed, Space-Free File Path
    // ----------------------------------------------------
    <div 
      ref={ref} 
      className="
        min-h-screen flex flex-col items-center justify-center 
        bg-cover bg-center bg-fixed bg-no-repeat 
        // 👇 USING THE RENAMED, RELIABLE PATH
        bg-[url('/whispering_library_bg.jpg')] 
        relative 
      "
    >
      
      {/* Dark Overlay (Opacity 30% for testing visibility) */}
      <div className="absolute inset-0 bg-black opacity-30"></div> 

      <section className="
        relative z-10 
        bg-transparent 
        flex flex-col items-center justify-center text-center
        p-8 rounded-lg 
      ">
        
        {/* LOGO IMAGE */}
        <img 
            src="/The whispering lib.png" 
            alt="The whispering lib" 
            className="mx-auto mb-6 w-[400px] h-auto max-w-full image-neon-gold"
        />
        
        {/* INTRODUCTORY TEXT */}
        <p className="text-white max-w-prose pt-1 leading-6 font-medium text-shadow-md">
        </p>

        {/* BUTTON */}
        <Button 
          variant="primary" 
          size="lg" 
          onClick={onStartCall} 
         className="mt-6 w-64 font-mono 
                     bg-neon-gold hover:bg-neon-gold-hover 
                     border-2 border-neon-gold 
                     shadow-neon-gold-light 
                     text-glow-neon-white"
        >
          ENTER THE VOID
        </Button>
      </section>
    </div>
  );
};