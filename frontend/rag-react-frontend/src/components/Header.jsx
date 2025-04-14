import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
        <h1 className="text-3xl font-semibold tracking-tight">
          <Link to="/" className="hover:underline transition-all duration-300 ease-in-out transform hover:scale-105">
            🧠 RAG Platform
          </Link>
        </h1>
        <span className="text-sm text-opacity-80 font-light tracking-wide">
          Multi-model Agent Chatbot using FastAPI & Langchain
        </span>
      </div>
    </header>
  );
}
