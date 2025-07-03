import Link from "next/link";

export default function Landing() {
  return (
    <div className="min-h-screen pt-32 px-6 max-w-[1400px] mx-auto grid grid-cols-12 gap-4">
      
      {/* Decorative Top SKU */}
      <div className="col-span-12 flex justify-between border-b border-white/10 pb-4 mb-12">
        <span className="font-sans text-xs tracking-widest text-muted">MEDICAL AI DIVISION</span>
        <span className="font-sans text-xs tracking-widest text-primary">2025 SKU S00191</span>
      </div>

      {/* Main Headline - Huge Serif */}
      <div className="col-span-12 lg:col-span-8 z-10">
        <h1 className="font-serif text-[5rem] md:text-[8rem] leading-[0.85] text-primary tracking-tight mb-8">
          <span className="block text-white">Efficient</span>
          <span className="block italic ml-12">NetB4</span>
          <span className="block">Detection</span>
        </h1>
      </div>

      {/* Floating Image / Abstract Element */}
      <div className="col-span-12 lg:col-span-4 relative mt-12 lg:mt-0">
        <div className="aspect-[3/4] bg-surface relative overflow-hidden thin-border">
            {/* Abstract visual representing a scan */}
            <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent opacity-80 z-10" />
             {/* You would replace this div with an <Image> of a CT scan or abstract art */}
            <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center grayscale contrast-125 hover:scale-105 transition-transform duration-700" />
        </div>
        <p className="font-serif text-2xl mt-4 text-right italic text-white">
          "Sensing the unseen."
        </p>
      </div>

      {/* Bottom Description & CTA */}
      <div className="col-span-12 lg:col-span-6 lg:col-start-1 mt-12 lg:-mt-24 space-y-8">
        <p className="font-sans text-muted text-lg leading-relaxed max-w-md">
          Utilizing advanced computer vision architectures for high-accuracy lung cancer classification. 
          A diagnostic tool designed for precision and speed.
        </p>

        <div className="flex items-center gap-8">
            <Link href="/predict" className="group flex items-center gap-4">
                <span className="font-serif text-3xl text-white group-hover:text-primary transition-colors">Start Diagnosis</span>
                <div className="w-12 h-[1px] bg-white group-hover:bg-primary transition-colors" />
            </Link>
        </div>
      </div>
      
      {/* Footer Info */}
      
    </div>
  );
}