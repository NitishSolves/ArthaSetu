import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { MinimumDataRequired as MIN_REQUIRED } from "@/lib/dataRequirements";

interface MinimumDataRequiredProps {
  featureName: string;
}

const MinimumDataRequired = ({ featureName }: MinimumDataRequiredProps) => {
  const navigate = useNavigate();

  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-amber-900">
          <AlertCircle className="h-5 w-5" />
          Insufficient Data
        </CardTitle>
        <CardDescription>
          This feature requires at least {MIN_REQUIRED} transactions to provide accurate analysis.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>More data needed</AlertTitle>
          <AlertDescription>
            To use {featureName}, please add at least {MIN_REQUIRED} transactions. 
            You can add transactions from the Transactions page.
          </AlertDescription>
        </Alert>
        <Button 
          onClick={() => navigate("/transactions")}
          className="w-full sm:w-auto"
        >
          Go to Transactions
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
};

export default MinimumDataRequired;

