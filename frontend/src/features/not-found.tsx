import { Link } from "react-router-dom";
import { Compass } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared";

export function NotFoundPage() {
  return (
    <EmptyState
      icon={Compass}
      title="Page not found"
      hint="The page you're looking for doesn't exist."
      action={<Button asChild><Link to="/">Back to dashboard</Link></Button>}
      className="py-24"
    />
  );
}
