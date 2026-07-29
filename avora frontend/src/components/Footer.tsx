export function Footer() {
  return (
    <footer className="relative border-t border-white/[0.06] py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <h3 className="text-xl font-bold text-white">
            Pratik Ojha
          </h3>
          <p className="text-xs leading-relaxed text-gray-500 max-w-md">
            Built with passion by Pratik Ojha. Independent AI project built with passion in Nepal.
          </p>
          <p className="text-[11px] text-gray-600">
            © {new Date().getFullYear()} AVORA. Independent project. Not a company.
          </p>
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="text-gray-500 hover:text-white transition-colors text-sm"
          >
            Back to Top ↑
          </button>
        </div>
      </div>
    </footer>
  );
}
