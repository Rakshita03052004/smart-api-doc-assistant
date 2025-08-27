import { useState, useEffect } from "react";

// Simple markdown renderer without external dependencies
function MarkdownRenderer({ content }) {
  const renderMarkdown = (text) => {
    if (!text) return "";
    
    return text
      // Headers
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-gray-800 mt-6 mb-3">$1</h3>')
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-gray-900 mt-8 mb-4">$1</h2>')
      .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-gray-900 mt-8 mb-6">$1</h1>')
      
      // Bold and italic
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      
      // Code blocks and inline code
      .replace(/```[\s\S]*?```/g, '') // Remove code blocks for now
      .replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">$1</code>')
      
      // Lists
      .replace(/^[\s]*[-\*\+]\s+(.*$)/gm, '<li class="ml-4 mb-1">• $1</li>')
      
      // Links (basic)
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:text-blue-800 underline">$1</a>')
      
      // Line breaks
      .replace(/\n\n/g, '</p><p class="mb-4">')
      .replace(/\n/g, '<br/>');
  };

  return (
    <div 
      className="prose max-w-none"
      dangerouslySetInnerHTML={{ 
        __html: `<p class="mb-4">${renderMarkdown(content)}</p>` 
      }} 
    />
  );
}

// Table renderer for API data
function TableRenderer({ content }) {
  const lines = content.split('\n').filter(line => line.trim());
  if (lines.length < 3) return <MarkdownRenderer content={content} />;
  
  // Check if it's a table
  const headerLine = lines.find(line => line.includes('|'));
  if (!headerLine) return <MarkdownRenderer content={content} />;
  
  const tableLines = lines.filter(line => line.includes('|') && !line.includes('---'));
  if (tableLines.length < 2) return <MarkdownRenderer content={content} />;
  
  const headers = tableLines[0].split('|').map(h => h.trim()).filter(h => h);
  const rows = tableLines.slice(1).map(line => 
    line.split('|').map(cell => cell.trim()).filter(cell => cell)
  );
  
  return (
    <div className="overflow-x-auto mb-6">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            {headers.map((header, i) => (
              <th key={i} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3 text-sm text-gray-900 border-b">
                  {cell.startsWith('`') && cell.endsWith('`') ? (
                    <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs font-mono">
                      {cell.slice(1, -1)}
                    </code>
                  ) : cell.includes('**') ? (
                    <span className="font-semibold">
                      {cell.replace(/\*\*(.*?)\*\*/g, '$1')}
                    </span>
                  ) : cell === '✅' ? (
                    <span className="text-green-600 font-bold">✅</span>
                  ) : cell === '❌' ? (
                    <span className="text-red-600 font-bold">❌</span>
                  ) : (
                    cell
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Mermaid diagram renderer
function MermaidDiagram({ chart }) {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const renderMermaid = async () => {
      try {
        const mermaid = (await import("https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.1/mermaid.esm.min.mjs")).default;
        
        mermaid.initialize({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
          }
        });

        const { svg } = await mermaid.render(`mermaid-${Date.now()}`, chart);
        setSvg(svg);
        setError("");
      } catch (err) {
        console.error("Mermaid render error:", err);
        setError("Could not render diagram");
      }
    };

    if (chart) {
      renderMermaid();
    }
  }, [chart]);

  if (error) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <div className="text-4xl mb-3">📊</div>
        <p className="text-blue-800 font-medium">Flow Diagram</p>
        <p className="text-blue-600 text-sm mt-1">Diagram visualization in progress...</p>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <div className="animate-spin text-2xl mb-2">⚙️</div>
        <p className="text-gray-600">Rendering flow diagram...</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 overflow-x-auto">
      <div dangerouslySetInnerHTML={{ __html: svg }} />
    </div>
  );
}

// Enhanced file upload component
function FileUploadZone({ onFileSelect, selectedFile, onUpload, isUploading, status }) {
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  return (
    <div className="mb-8">
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 transition-all duration-300 ${
          dragOver
            ? "border-blue-500 bg-blue-50"
            : selectedFile
            ? "border-green-400 bg-green-50"
            : "border-gray-300 hover:border-blue-400 bg-gray-50"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="text-center">
          <div className="text-5xl mb-4">
            {selectedFile ? "📄" : dragOver ? "📥" : "📋"}
          </div>
          
          {selectedFile ? (
            <div className="space-y-3">
              <p className="text-lg font-semibold text-green-800">
                File Ready: {selectedFile.name}
              </p>
              <p className="text-sm text-green-600">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
              <button
                onClick={onUpload}
                disabled={isUploading}
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  isUploading
                    ? "bg-gray-400 text-white cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 text-white transform hover:scale-105"
                }`}
              >
                {isUploading ? "🔄 Analyzing..." : "🚀 Analyze API"}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-gray-800">
                Drop your API specification here
              </h3>
              <p className="text-gray-600">
                OpenAPI, Swagger, Postman, or custom JSON/YAML
              </p>
              <input
                type="file"
                accept=".json,.yaml,.yml,.txt"
                onChange={(e) => e.target.files[0] && onFileSelect(e.target.files[0])}
                className="hidden"
                id="file-input"
              />
              <label
                htmlFor="file-input"
                className="inline-block px-6 py-3 bg-white border-2 border-blue-500 text-blue-600 rounded-lg font-semibold cursor-pointer hover:bg-blue-50 transition-colors"
              >
                Choose File
              </label>
            </div>
          )}
        </div>
      </div>

      {status && (
        <div className={`mt-4 p-4 rounded-lg border-l-4 ${
          status.success
            ? "bg-green-50 border-green-500 text-green-800"
            : "bg-red-50 border-red-500 text-red-800"
        }`}>
          <p className="font-semibold">{status.message}</p>
          {status.details && <p className="text-sm mt-1">{status.details}</p>}
        </div>
      )}
    </div>
  );
}

// Search component
function SearchBox({ onSearch, isSearching, hasSpec }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  if (!hasSpec) return null;

  return (
    <div className="mb-6">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Search endpoints, parameters, descriptions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <span className="text-gray-400">🔍</span>
          </div>
        </div>
        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            isSearching || !query.trim()
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
        >
          {isSearching ? "⏳" : "Search"}
        </button>
      </form>
    </div>
  );
}

// Main app component
export default function SmartAPIDoc() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [summary, setSummary] = useState("");
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [apiInfo, setApiInfo] = useState(null);

  const API_URL = "http://127.0.0.1:8000";

  // Upload handler
  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      setUploadStatus(null);

      const response = await fetch(`${API_URL}/upload-spec`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setUploadStatus({
        success: true,
        message: `✅ Successfully processed: ${data.title}`,
        details: `${data.path_count} endpoints • Version ${data.version}`
      });

      setApiInfo({
        title: data.title,
        version: data.version,
        endpoints: data.path_count,
        hasAuth: data.has_auth
      });

      // Auto-load summary
      setTimeout(loadSummary, 500);

    } catch (error) {
      setUploadStatus({
        success: false,
        message: "Upload failed: " + error.message,
        details: "Please check your file format and try again."
      });
    } finally {
      setUploading(false);
    }
  };

  // Load summary
  const loadSummary = async () => {
    try {
      setLoadingSummary(true);
      const response = await fetch(`${API_URL}/api-summary`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to load summary');
      }

      const summaryText = await response.text();
      setSummary(summaryText);
      setActiveTab("overview");

    } catch (error) {
      setSummary(`❌ Error: ${error.message}\n\nPlease upload a valid API specification.`);
    } finally {
      setLoadingSummary(false);
    }
  };

  // Search handler
  const handleSearch = async (keyword) => {
    try {
      setSearching(true);
      const response = await fetch(`${API_URL}/search?keyword=${encodeURIComponent(keyword)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Search failed');
      }

      setSearchResults(data);
      setActiveTab("search");

    } catch (error) {
      setSearchResults({
        keyword,
        total_matches: 0,
        endpoints: {},
        error: error.message
      });
    } finally {
      setSearching(false);
    }
  };

  // Parse markdown sections
  const parseSections = (markdown) => {
    const sections = {
      overview: "",
      endpoints: "",
      parameters: "",
      auth: "",
      flow: ""
    };

    if (!markdown) return sections;

    // Split by main headers
    const overviewMatch = markdown.match(/# 📊[\s\S]*?(?=## 🔗|$)/);
    const endpointsMatch = markdown.match(/## 🔗 Endpoints[\s\S]*?(?=## ⚙️|$)/);
    const paramsMatch = markdown.match(/## ⚙️ Parameters[\s\S]*?(?=## 🔐|$)/);
    const authMatch = markdown.match(/## 🔐 Authentication[\s\S]*?(?=## 🔄|$)/);
    const flowMatch = markdown.match(/## 🔄 API Flow[\s\S]*$/);

    sections.overview = overviewMatch ? overviewMatch[0] : markdown;
    sections.endpoints = endpointsMatch ? endpointsMatch[0] : "";
    sections.parameters = paramsMatch ? paramsMatch[0] : "";
    sections.auth = authMatch ? authMatch[0] : "";
    sections.flow = flowMatch ? flowMatch[0] : "";

    return sections;
  };

  const sections = parseSections(summary);

  // Extract Mermaid chart from flow section
  const extractMermaidChart = (text) => {
    const match = text.match(/```mermaid\n([\s\S]*?)\n```/);
    return match ? match[1] : null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-6 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            🧠 Smart API Assistant
          </h1>
          <p className="text-xl text-gray-600">
            Transform any API specification into beautiful documentation
          </p>
        </div>

        {/* File Upload */}
        <FileUploadZone
          onFileSelect={setFile}
          selectedFile={file}
          onUpload={handleUpload}
          isUploading={uploading}
          status={uploadStatus}
        />

        {/* API Info Cards */}
        {apiInfo && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg p-4 border-l-4 border-blue-500">
              <p className="text-sm text-gray-600">API Title</p>
              <p className="font-bold text-gray-900 truncate">{apiInfo.title}</p>
            </div>
            <div className="bg-white rounded-lg p-4 border-l-4 border-green-500">
              <p className="text-sm text-gray-600">Version</p>
              <p className="font-bold text-gray-900">{apiInfo.version}</p>
            </div>
            <div className="bg-white rounded-lg p-4 border-l-4 border-purple-500">
              <p className="text-sm text-gray-600">Endpoints</p>
              <p className="font-bold text-gray-900">{apiInfo.endpoints}</p>
            </div>
            <div className="bg-white rounded-lg p-4 border-l-4 border-orange-500">
              <p className="text-sm text-gray-600">Security</p>
              <p className="font-bold text-gray-900">{apiInfo.hasAuth ? "🔐 Protected" : "🌐 Public"}</p>
            </div>
          </div>
        )}

        {/* Search Box */}
        <SearchBox 
          onSearch={handleSearch}
          isSearching={searching}
          hasSpec={!!summary}
        />

        {/* Loading State */}
        {loadingSummary && (
          <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
            <div className="animate-spin text-4xl mb-4">⚙️</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              Analyzing API Specification
            </h3>
            <p className="text-gray-600">
              Extracting endpoints, generating diagrams, and preparing insights...
            </p>
          </div>
        )}

        {/* Main Content */}
        {(summary || searchResults) && !loadingSummary && (
          <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
            {/* Tabs */}
            <div className="border-b bg-gray-50">
              <div className="flex overflow-x-auto">
                {[
                  { id: "overview", label: "📊 Overview" },
                  { id: "endpoints", label: "🔗 Endpoints" },
                  { id: "parameters", label: "⚙️ Parameters" },
                  { id: "auth", label: "🔐 Auth" },
                  { id: "flow", label: "🔄 Flow" },
                  { id: "search", label: `🔍 Search${searchResults?.total_matches ? ` (${searchResults.total_matches})` : ""}` }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-6 py-4 font-medium text-sm whitespace-nowrap border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? "border-blue-500 text-blue-600 bg-white"
                        : "border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              {activeTab === "search" && searchResults ? (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold">
                      Search Results for "{searchResults.keyword}"
                    </h2>
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                      {searchResults.total_matches} matches
                    </span>
                  </div>

                  {searchResults.error ? (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                      <h3 className="font-semibold text-red-800 mb-2">Search Error</h3>
                      <p className="text-red-700">{searchResults.error}</p>
                    </div>
                  ) : searchResults.total_matches === 0 ? (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                      <div className="text-4xl mb-4">🔍</div>
                      <h3 className="font-semibold text-yellow-800 mb-2">No Results Found</h3>
                      <p className="text-yellow-700">Try different keywords or check your search term.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* Endpoints Results */}
                      {Object.keys(searchResults.endpoints).length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold mb-4">📡 Matching Endpoints</h3>
                          <div className="space-y-4">
                            {Object.entries(searchResults.endpoints).map(([path, methods]) => (
                              <div key={path} className="border border-gray-200 rounded-lg p-6 hover:shadow-sm transition-shadow">
                                <div className="font-mono text-sm bg-gray-100 px-3 py-2 rounded mb-4">
                                  {path}
                                </div>
                                <div className="grid gap-3">
                                  {Object.entries(methods).map(([method, details]) => (
                                    <div key={method} className="flex items-start gap-4">
                                      <span className={`px-3 py-1 rounded text-xs font-bold text-white ${
                                        method.toLowerCase() === 'get' ? 'bg-green-500' :
                                        method.toLowerCase() === 'post' ? 'bg-blue-500' :
                                        method.toLowerCase() === 'put' ? 'bg-orange-500' :
                                        method.toLowerCase() === 'delete' ? 'bg-red-500' : 'bg-gray-500'
                                      }`}>
                                        {method.toUpperCase()}
                                      </span>
                                      <div className="flex-1">
                                        <p className="font-medium text-gray-900">
                                          {details.summary || "No title"}
                                        </p>
                                        {details.description && (
                                          <p className="text-sm text-gray-600 mt-1">
                                            {details.description}
                                          </p>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Components Results */}
                      {Object.keys(searchResults.components || {}).length > 0 && (
                        <div>
                          <h3 className="text-lg font-semibold mb-4">🧩 Matching Components</h3>
                          <div className="grid gap-4">
                            {Object.entries(searchResults.components).map(([key, comp]) => (
                              <div key={key} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                                    {comp.type}
                                  </span>
                                  <span className="font-mono text-sm">{comp.name}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : activeTab === "flow" && sections.flow ? (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">🔄 API Flow Diagram</h2>
                  <p className="text-gray-600 mb-6">Visual representation of your API's main operations and flow.</p>
                  
                  {extractMermaidChart(sections.flow) ? (
                    <MermaidDiagram chart={extractMermaidChart(sections.flow)} />
                  ) : (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
                      <div className="text-4xl mb-4">📊</div>
                      <h3 className="font-semibold text-blue-800 mb-2">Flow Diagram Available</h3>
                      <p className="text-blue-600">The API flow visualization is ready to display.</p>
                    </div>
                  )}
                </div>
              ) : activeTab === "endpoints" && sections.endpoints ? (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">🔗 API Endpoints</h2>
                  <TableRenderer content={sections.endpoints} />
                </div>
              ) : (
                <div>
                  {sections[activeTab] ? (
                    sections[activeTab].includes('|') && sections[activeTab].includes('---') ? (
                      <TableRenderer content={sections[activeTab]} />
                    ) : (
                      <MarkdownRenderer content={sections[activeTab]} />
                    )
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-4xl mb-4">📋</div>
                      <h3 className="text-lg font-semibold text-gray-800 mb-2">
                        No {activeTab} data available
                      </h3>
                      <p className="text-gray-600">
                        Upload a valid API specification to see {activeTab} information.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Welcome State */}
        {!summary && !loadingSummary && !uploadStatus && (
          <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
            <div className="text-6xl mb-6">🚀</div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Ready to Transform Your API Documentation
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Upload any API specification and get instant insights, clean documentation, and interactive flow diagrams.
            </p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-2xl mx-auto">
              {[
                { icon: "📄", name: "OpenAPI", desc: "3.x & 2.x" },
                { icon: "📋", name: "Swagger", desc: "JSON/YAML" },
                { icon: "📮", name: "Postman", desc: "Collections" },
                { icon: "💤", name: "Insomnia", desc: "Export files" }
              ].map((format) => (
                <div key={format.name} className="p-4 rounded-lg border-2 border-dashed border-gray-200 hover:border-blue-300 transition-colors">
                  <div className="text-3xl mb-2">{format.icon}</div>
                  <div className="font-semibold text-gray-900">{format.name}</div>
                  <div className="text-sm text-gray-600">{format.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}