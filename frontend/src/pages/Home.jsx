const features = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
    title: "Fast Redirects",
    description:
      "Lightning-fast redirects powered by a global edge network. Your users won't notice the redirect.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
    title: "Click Analytics",
    description:
      "Track every click with detailed analytics. Know exactly how your links are performing in real time.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 4v1m6 11h2m-6 0h-2m4 0a9.956 9.956 0 01-7 3 9.956 9.956 0 01-7-3m14 0a9.956 9.956 0 00-7-3 9.956 9.956 0 00-7 3m14 0H6"
        />
      </svg>
    ),
    title: "QR Codes",
    description:
      "Generate QR codes for every shortened URL. Perfect for print, business cards, and marketing materials.",
  },
];

export default function Home() {
  return (
    <div className="animate-[fadeIn_0.5s_ease-out]">
      <section className="pt-20 pb-16 sm:pt-28 sm:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/5 border border-primary/10 text-primary text-sm font-medium mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
            </span>
            Now in Public Beta
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-text max-w-4xl mx-auto leading-tight">
            Shorten your links,{" "}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              amplify your reach
            </span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
            DevShort is the modern way to shorten URLs, generate QR codes, and
            track clicks. Built for developers, designed for everyone.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a href="#cta" className="btn-primary text-lg px-8 py-3.5">
              Get Started Free
            </a>
            <a
              href="#features"
              className="btn-secondary text-lg px-8 py-3.5"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      <section id="features" className="py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-text tracking-tight">
              Everything you need
            </h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
              Powerful features to manage, share, and track your links&mdash;all
              in one place.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="card group hover:-translate-y-1 transition-transform duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-5 group-hover:bg-primary group-hover:text-white transition-colors duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-text mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-500 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="cta" className="py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-secondary p-10 sm:p-16 text-center">
            <div className="absolute inset-0 bg-black/10" />
            <div className="relative z-10">
              <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
                Ready to shorten your first link?
              </h2>
              <p className="mt-4 text-lg text-white/80 max-w-lg mx-auto">
                Join thousands of developers and marketers who trust DevShort
                for their URL management.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto">
                <input
                  type="url"
                  placeholder="Paste your long URL here..."
                  className="w-full px-5 py-3.5 rounded-xl bg-white text-text placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all"
                />
                <button className="w-full sm:w-auto btn-primary bg-white text-primary hover:bg-gray-50 hover:text-primary-700 whitespace-nowrap px-8 py-3.5">
                  Shorten URL
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
