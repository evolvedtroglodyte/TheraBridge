export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t bg-white">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-gray-500">
            &copy; {currentYear} Audio Transcription Pipeline. All rights reserved.
          </p>

          <div className="flex gap-6 text-sm text-gray-500">
            <a
              href="#"
              className="hover:text-primary transition-colors"
              aria-label="Privacy Policy"
            >
              Privacy
            </a>
            <a
              href="#"
              className="hover:text-primary transition-colors"
              aria-label="Terms of Service"
            >
              Terms
            </a>
            <a
              href="#"
              className="hover:text-primary transition-colors"
              aria-label="Documentation"
            >
              Docs
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
