export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-sm text-gray-400">
          &copy; {new Date().getFullYear()} DevShort &mdash; Modern URL Shortener
        </p>
      </div>
    </footer>
  );
}
