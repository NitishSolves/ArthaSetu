import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageIntroProps = {
  title: string;
  description: string;
  className?: string;
};

const PageIntro: React.FC<PageIntroProps> = ({ title, description, className }) => {
  return (
    <div
      className={cn(
        "bg-muted/30 border border-border/40 rounded-[6px] p-4 mb-6",
        className
      )}
    >
      <h3 className="text-[14px] font-semibold text-foreground mb-1.5">{title}</h3>
      <p className="text-[13px] text-muted-foreground leading-relaxed line-clamp-2">{description}</p>
    </div>
  );
};

export default PageIntro;

