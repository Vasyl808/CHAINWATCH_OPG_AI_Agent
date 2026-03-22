import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { HomePage } from "@/pages/HomePage";

function App() {
  return (
    <div className="relative min-h-screen text-gray-900 selection:bg-brand-200 selection:text-brand-900 flex flex-col">
      <Header />
      <div className="flex-1">
        <HomePage />
      </div>
      <Footer />
    </div>
  );
}

export default App;
