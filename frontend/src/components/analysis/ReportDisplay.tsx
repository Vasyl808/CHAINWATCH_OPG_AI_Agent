import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Download, RotateCcw, CheckCircle } from "lucide-react";
import { CyberPanel } from "@/components/ui/CyberPanel";
import { shortenAddress } from "@/utils";

interface Props {
  report: string;
  address: string;
  onReset: () => void;
}

export function ReportDisplay({ report, address, onReset }: Props) {
  const handleDownload = () => {
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chainwatch-${address.slice(0, 10)}-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="w-full space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h2 className="font-sans text-lg font-bold text-gray-900 tracking-tight">
              Analysis Complete
            </h2>
            <p className="font-sans text-xs font-medium text-gray-500 mt-0.5">
              Wallet: {shortenAddress(address)}
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleDownload}
            className="btn-ghost"
          >
            <Download className="w-4 h-4 mr-2" />
            <span>Export</span>
          </button>
          <button
            onClick={onReset}
            className="btn-primary"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            <span>New Scan</span>
          </button>
        </div>
      </div>

      {/* Report */}
      <CyberPanel
        label="Security Intelligence Report"
        accent="cyan"
        className="p-8"
      >
        <div className="report-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({ ...props }) => (
                <div className="table-wrapper">
                  <table {...props} />
                </div>
              ),
            }}
          >
            {report}
          </ReactMarkdown>
        </div>
      </CyberPanel>
    </motion.div>
  );
}
