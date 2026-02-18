import { Button } from "@/components/ui/button";
import Icon from "@/components/ui/icon";

interface HeroSectionProps {
  onNavigate: (section: string) => void;
}

const HeroSection = ({ onNavigate }: HeroSectionProps) => {
  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center grid-bg overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-neon-purple/5 via-transparent to-background" />

      <div className="absolute top-20 left-10 w-72 h-72 bg-neon-purple/10 rounded-full blur-[100px] animate-pulse-neon" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-neon-cyan/10 rounded-full blur-[120px] animate-pulse-neon" style={{ animationDelay: "1s" }} />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-neon-pink/5 rounded-full blur-[150px]" />

      <div className="container relative z-10 mx-auto px-4 text-center">
        <div className="animate-fade-in">
          <div className="inline-flex items-center gap-2 bg-neon-purple/10 border border-neon-purple/30 rounded-full px-4 py-2 mb-8">
            <span className="w-2 h-2 bg-neon-green rounded-full animate-pulse-neon" />
            <span className="text-sm font-rubik text-neon-purple">Новые скрипты каждую неделю</span>
          </div>
        </div>

        <h1 className="font-orbitron font-black text-4xl sm:text-5xl md:text-7xl mb-6 animate-fade-in" style={{ animationDelay: "0.1s" }}>
          <span className="text-foreground">Лучшие</span>{" "}
          <span className="text-neon-purple neon-glow-purple">скрипты</span>
          <br />
          <span className="text-foreground">для</span>{" "}
          <span className="text-neon-cyan neon-glow-cyan">Roblox</span>
        </h1>

        <p className="font-rubik text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto mb-10 animate-fade-in" style={{ animationDelay: "0.2s" }}>
          Проверенные скрипты с мгновенной доставкой. Автофарм, ESP, Aimbot и другие решения для твоих любимых игр.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in" style={{ animationDelay: "0.3s" }}>
          <Button
            size="lg"
            className="bg-neon-purple hover:bg-neon-purple/80 text-white font-rubik font-semibold text-base px-8 neon-border"
            onClick={() => onNavigate("catalog")}
          >
            <Icon name="Gamepad2" size={20} />
            Смотреть каталог
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="border-neon-cyan/50 text-neon-cyan hover:bg-neon-cyan/10 font-rubik font-semibold text-base px-8"
            onClick={() => onNavigate("pricing")}
          >
            <Icon name="Zap" size={20} />
            Тарифы
          </Button>
        </div>

        <div className="flex justify-center gap-8 mt-16 animate-fade-in" style={{ animationDelay: "0.4s" }}>
          {[
            { value: "500+", label: "Скриптов" },
            { value: "10K+", label: "Клиентов" },
            { value: "24/7", label: "Поддержка" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="font-orbitron font-bold text-2xl md:text-3xl text-neon-cyan">{stat.value}</div>
              <div className="font-rubik text-sm text-muted-foreground mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-float">
        <Icon name="ChevronDown" size={28} className="text-muted-foreground" />
      </div>
    </section>
  );
};

export default HeroSection;
