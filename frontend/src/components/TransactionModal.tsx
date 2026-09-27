import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useApp } from "@/contexts/AppContext";
import { toast } from "sonner";

interface TransactionModalProps {
  open: boolean;
  onClose: () => void;
}

const TransactionModal = ({ open, onClose }: TransactionModalProps) => {
  const { addTransaction } = useApp();
  const [type, setType] = useState<"income" | "expense">("expense");
  const [category, setCategory] = useState("");
  const [amount, setAmount] = useState("");

  const incomeCategories = ["Uber", "Ola", "Swiggy", "Zomato", "Freelance", "Other"];
  const expenseCategories = ["Fuel", "Food", "Maintenance", "Phone", "Rent", "Other"];

  const handleSubmit = () => {
    if (!category || !amount) {
      toast.error("Please fill all fields");
      return;
    }

    const now = new Date();
    addTransaction({
      type,
      category,
      amount: parseFloat(amount),
      time: now.toTimeString().slice(0, 5), // HH:mm -- transaction_time is a Postgres `time` column
      date: now.toISOString().split("T")[0],
    });

    toast.success(`${type === "income" ? "Income" : "Expense"} added successfully`);
    setCategory("");
    setAmount("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Transaction</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label>Type</Label>
            <Select value={type} onValueChange={(v) => setType(v as "income" | "expense")}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="income">Income</SelectItem>
                <SelectItem value="expense">Expense</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {(type === "income" ? incomeCategories : expenseCategories).map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Amount (₹)</Label>
            <Input
              type="number"
              placeholder="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>

          <div className="flex gap-2 pt-2">
            <Button variant="outline" className="flex-1" onClick={onClose}>
              Cancel
            </Button>
            <Button className="flex-1 bg-primary" onClick={handleSubmit}>
              Add
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TransactionModal;
