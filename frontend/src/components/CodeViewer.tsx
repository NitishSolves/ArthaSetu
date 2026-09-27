import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Copy, Check, Code2, Eye, EyeOff } from 'lucide-react';

interface CodeViewerProps {
  title: string;
  description: string;
  code: string;
  language?: string;
  className?: string;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  title,
  description,
  code,
  language = 'javascript',
  className
}) => {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  const displayCode = isExpanded ? code : code.slice(0, 300) + (code.length > 300 ? '...' : '');

  return (
    <Card className={`overflow-hidden ${className}`}>
      <div className="p-4 border-b border-border">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-foreground mb-1">{title}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              {language}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={copyToClipboard}
              className="h-8 w-8 p-0"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </Button>
          </div>
        </div>
      </div>
      
      <div className="relative">
        <pre className="p-4 overflow-x-auto bg-muted/30 text-sm">
          <code className="text-foreground">{displayCode}</code>
        </pre>
        
        {code.length > 300 && (
          <div className="absolute bottom-2 right-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-7 text-xs"
            >
              {isExpanded ? (
                <>
                  <EyeOff size={12} className="mr-1" />
                  Collapse
                </>
              ) : (
                <>
                  <Eye size={12} className="mr-1" />
                  Expand
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};

export default CodeViewer;