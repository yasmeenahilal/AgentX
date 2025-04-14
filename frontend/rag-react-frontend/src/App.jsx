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
