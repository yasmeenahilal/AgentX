# #!/bin/bash

# # === CONFIG ===
# PROJECT_NAME="rag-react-frontend"

# # === CREATE PROJECT ===
# npm create vite@latest "$PROJECT_NAME" -- --template react
# cd "$PROJECT_NAME" || exit

# # === INSTALL DEPENDENCIES ===
# npm install
# npm install -D tailwindcss postcss autoprefixer
# npx tailwindcss init -p
# npm install react-router-dom

# # === CONFIGURE TAILWIND ===
# cat > tailwind.config.js <<EOF
# export default {
#   content: [
#     "./index.html",
#     "./src/**/*.{js,ts,jsx,tsx}",
#   ],
#   theme: {
#     extend: {},
#   },
#   plugins: [],
# }
# EOF

# cat > src/index.css <<EOF
# @tailwind base;
# @tailwind components;
# @tailwind utilities;
# EOF

# # === CREATE FOLDER STRUCTURE ===
# mkdir -p src/components src/pages

# # === LAYOUT COMPONENTS ===
# cat > src/components/Layout.jsx <<'EOF'
# import Header from './Header';
# import Sidebar from './Sidebar';
# import Footer from './Footer';

# export default function Layout({ children }) {
#   return (
#     <div className="bg-gray-100 text-gray-800 min-h-screen flex flex-col">
#       <Header />
#       <div className="flex flex-1">
#         <Sidebar />
#         <main className="flex-1 p-6">{children}</main>
#       </div>
#       <Footer />
#     </div>
#   );
# }
# EOF

# cat > src/components/Header.jsx <<'EOF'
# import { Link } from 'react-router-dom';

# export default function Header() {
#   return (
#     <header className="bg-blue-700 text-white shadow-md">
#       <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
#         <h1 className="text-2xl font-bold">
#           <Link to="/" className="hover:underline">
#             🧠 RAG Platform
#           </Link>
#         </h1>
#         <span className="text-sm">Multi-model Agent Chatbot using FastAPI & Langchain</span>
#       </div>
#     </header>
#   );
# }
# EOF

# cat > src/components/Sidebar.jsx <<'EOF'
# import { NavLink } from 'react-router-dom';

# const links = [
#   { path: "/", label: "🏠 Home" },
#   { path: "/upload", label: "📁 Upload Data" },
#   { path: "/create-agent", label: "🤖 Create Agent" },
#   { path: "/list-agents", label: "📋 List Agents" },
#   { path: "/delete-agent", label: "🗑️ Delete Agent" },
#   { path: "/ask-agent", label: "💬 Ask Agent" }
# ];

# export default function Sidebar() {
#   return (
#     <aside className="w-64 bg-white shadow-lg hidden md:block">
#       <div className="p-6">
#         <h2 className="text-xl font-semibold mb-6 text-blue-600">Navigation</h2>
#         <nav className="space-y-2">
#           {links.map(link => (
#             <NavLink
#               key={link.path}
#               to={link.path}
#               className={({ isActive }) =>
#                 `block py-2 px-4 rounded hover:bg-blue-100 ${
#                   isActive ? "bg-blue-100 font-semibold text-blue-700" : ""
#                 }`
#               }
#             >
#               {link.label}
#             </NavLink>
#           ))}
#         </nav>
#       </div>
#     </aside>
#   );
# }
# EOF

# cat > src/components/Footer.jsx <<'EOF'
# export default function Footer() {
#   return (
#     <footer className="bg-white text-gray-500 text-center py-4 shadow-inner">
#       &copy; 2025 RAG Platform. Built with ❤️ using FastAPI & Langchain.
#     </footer>
#   );
# }
# EOF

# # === ROUTING SETUP ===
# cat > src/App.jsx <<'EOF'
# import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
# import Layout from './components/Layout';
# import Home from './pages/Home';
# import UploadData from './pages/UploadData';
# import CreateAgent from './pages/CreateAgent';
# import AskAgent from './pages/AskAgent';
# import DeleteAgent from './pages/DeleteAgent';
# import ListAgents from './pages/ListAgents';

# function App() {
#   return (
#     <Router>
#       <Layout>
#         <Routes>
#           <Route path="/" element={<Home />} />
#           <Route path="/upload" element={<UploadData />} />
#           <Route path="/create-agent" element={<CreateAgent />} />
#           <Route path="/ask-agent" element={<AskAgent />} />
#           <Route path="/delete-agent" element={<DeleteAgent />} />
#           <Route path="/list-agents" element={<ListAgents />} />
#         </Routes>
#       </Layout>
#     </Router>
#   );
# }

# export default App;
# EOF

# # === MAIN ENTRY POINT ===
# cat > src/main.jsx <<'EOF'
# import React from 'react'
# import ReactDOM from 'react-dom/client'
# import App from './App.jsx'
# import './index.css'

# ReactDOM.createRoot(document.getElementById('root')).render(
#   <React.StrictMode>
#     <App />
#   </React.StrictMode>
# )
# EOF

# # === PAGES ===
# for page in Home UploadData CreateAgent AskAgent DeleteAgent ListAgents
# do
# cat > "src/pages/$page.jsx" <<EOF
# export default function $page() {
#   return (
#     <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-4xl mx-auto">
#       <h1 className="text-3xl font-bold text-indigo-600 mb-4">$page</h1>
#       <p className="text-gray-600">This is the $page page. Add your form and logic here.</p>
#     </div>
#   );
# }
# EOF
# done

# # === DONE ===
# echo -e "\n✅ Project is ready!"
# echo "👉 cd $PROJECT_NAME"
# echo "👉 npm run dev -- --host"
#!/bin/bash

# === CONFIG ===
PROJECT_NAME="rag-react-frontend"

# === CREATE PROJECT ===
npm create vite@latest "$PROJECT_NAME" -- --template react
cd "$PROJECT_NAME" || exit

# === INSTALL DEPENDENCIES ===
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install react-router-dom

# === CONFIGURE TAILWIND ===
cat > tailwind.config.js <<EOF
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

cat > src/index.css <<EOF
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

# === CREATE FOLDER STRUCTURE ===
mkdir -p src/components src/pages

# === COMPONENT: Layout ===
cat > src/components/Layout.jsx <<'EOF'
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

export default function Layout({ children }) {
  return (
    <div className="flex flex-col min-h-screen bg-gray-100 text-gray-800">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6">{children}</main>
      </div>
      <Footer />
    </div>
  );
}
EOF

# === COMPONENT: Header ===
cat > src/components/Header.jsx <<'EOF'
import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="bg-blue-700 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          <Link to="/" className="hover:underline">🧠 RAG Platform</Link>
        </h1>
        <span className="text-sm">Multi-model Agent Chatbot using FastAPI & Langchain</span>
      </div>
    </header>
  );
}
EOF

# === COMPONENT: Sidebar ===
cat > src/components/Sidebar.jsx <<'EOF'
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
EOF

# === COMPONENT: Footer ===
cat > src/components/Footer.jsx <<'EOF'
export default function Footer() {
  return (
    <footer className="bg-white text-gray-500 text-center py-4 shadow-inner">
      &copy; 2025 RAG Platform. Built with ❤️ using FastAPI & Langchain.
    </footer>
  );
}
EOF

# === APP ROUTER SETUP ===
cat > src/App.jsx <<'EOF'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import UploadData from './pages/UploadData';
import CreateAgent from './pages/CreateAgent';
import AskAgent from './pages/AskAgent';
import DeleteAgent from './pages/DeleteAgent';
import ListAgents from './pages/ListAgents';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<UploadData />} />
          <Route path="/create-agent" element={<CreateAgent />} />
          <Route path="/ask-agent" element={<AskAgent />} />
          <Route path="/delete-agent" element={<DeleteAgent />} />
          <Route path="/list-agents" element={<ListAgents />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
EOF

# === ENTRY POINT ===
cat > src/main.jsx <<'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# === PAGES ===
for page in Home UploadData CreateAgent AskAgent DeleteAgent ListAgents
do
cat > "src/pages/$page.jsx" <<EOF
export default function $page() {
  return (
    <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-indigo-600 mb-4">$page</h1>
      <p className="text-gray-600">This is the $page page. Add your content here.</p>
    </div>
  );
}
EOF
done

# === DONE ===
echo -e "\n✅ React RAG Platform setup complete!"
echo "👉 cd $PROJECT_NAME"
echo "👉 npm run dev -- --host"
