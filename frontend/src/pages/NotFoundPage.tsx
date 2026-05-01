import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="container flex flex-col items-center justify-center min-h-[70vh] text-center space-y-6">
      <motion.div 
        className="p-6 bg-muted/50 rounded-full"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
      >
        <ShieldAlert className="h-16 w-16 text-muted-foreground" />
      </motion.div>
      <motion.div 
        className="space-y-2"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">404 - Not Found</h1>
        <p className="text-xl text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
      </motion.div>
      <motion.div 
        className="pt-6"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <Button asChild size="lg" className="rounded-full px-8 shadow-lg">
          <Link to="/">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Return to Home
          </Link>
        </Button>
      </motion.div>
    </div>
  );
}
