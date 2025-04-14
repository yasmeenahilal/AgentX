import { NavLink } from 'react-router-dom';

const links = [
  { path: "/", label: "🏠 Home" },
  { path: "/upload", label: "📁 Upload Data" },
  { path: "/create-agent", label: "🤖 Create Agent" },
  { path: "/list-agents", label: "📋 List Agents" },
  { path: "/delete-agent", label: "🗑️ Delete Agent" },
  { path: "/ask-agent", label: "💬 Ask Agent" }
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white shadow-lg hidden md:block">
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-6 text-blue-600">Navigation</h2>
        <nav className="space-y-2">
          {links.map(link => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `block py-2 px-4 rounded hover:bg-blue-100 ${
                  isActive ? "bg-blue-100 font-semibold text-blue-700" : ""
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
}
