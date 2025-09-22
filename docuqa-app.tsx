import React, { useState, useRef, useEffect } from 'react';
import { FileText, Upload, MessageCircle, Send, Loader2, X, Database, Search, Settings, BookOpen, Brain } from 'lucide-react';

const DocuQAApp = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [searchMode, setSearchMode] = useState('smart'); // 'smart', 'vector', 'keyword'
  const [temperature, setTemperature] = useState(0.3);
  const [documentDatabase, setDocumentDatabase] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isBuilding, setIsBuilding] = useState(false);
  const fileInputRef = useRef(null);

  // 시스템 프롬프트 - 사주명리 전문가 설정 가능
  const [systemPrompt, setSystemPrompt] = useState(
    "당신은 업로드된 문서를 기반으로 정확하고 자세한 답변을 제공하는 AI 어시스턴트입니다. 문서의 내용을 근거로 하여 답변하고, 근거를 명확히 제시해주세요."
  );

  // 문서 처리 및 데이터베이스 구축
  const processDocument = async (file) => {
    try {
      let textContent = '';
      
      if (file.type === 'application/pdf') {
        // PDF는 Claude API에서 직접 처리
        return {
          name: file.name,
          type: file.type,
          size: file.size,
          base64Data: file.base64Data,
          processed: false // PDF는 실시간 처리
        };
      } else {
        // 텍스트 파일 처리
        textContent = atob(file.base64Data);
        
        // 텍스트를 청크 단위로 분할 (RAG 스타일)
        const chunks = splitTextIntoChunks(textContent, 500);
        const processedChunks = chunks.map((chunk, index) => ({
          id: `${file.name}_chunk_${index}`,
          content: chunk,
          source: file.name,
          metadata: {
            filename: file.name,
            chunk_index: index,
            total_chunks: chunks.length
          }
        }));

        return {
          name: file.name,
          type: file.type,
          size: file.size,
          textContent: textContent,
          chunks: processedChunks,
          processed: true
        };
      }
    } catch (error) {
      console.error('문서 처리 오류:', error);
      throw error;
    }
  };

  // 텍스트를 청크로 분할하는 함수
  const splitTextIntoChunks = (text, chunkSize = 500) => {
    const sentences = text.split(/[.!?]\s+/);
    const chunks = [];
    let currentChunk = '';

    for (const sentence of sentences) {
      if (currentChunk.length + sentence.length > chunkSize && currentChunk.length > 0) {
        chunks.push(currentChunk.trim());
        currentChunk = sentence;
      } else {
        currentChunk += (currentChunk ? ' ' : '') + sentence;
      }
    }
    
    if (currentChunk) {
      chunks.push(currentChunk.trim());
    }

    return chunks.filter(chunk => chunk.length > 50); // 너무 짧은 청크 제외
  };

  // 벡터 유사도 검색 시뮬레이션 (간단한 키워드 매칭)
  const performVectorSearch = (query, k = 3) => {
    const allChunks = documentDatabase.flatMap(doc => doc.chunks || []);
    if (!allChunks.length) return [];

    // 간단한 키워드 기반 유사도 계산
    const queryWords = query.toLowerCase().split(/\s+/);
    const scoredChunks = allChunks.map(chunk => {
      const content = chunk.content.toLowerCase();
      const score = queryWords.reduce((acc, word) => {
        const matches = (content.match(new RegExp(word, 'g')) || []).length;
        return acc + matches;
      }, 0);
      
      return { ...chunk, score };
    });

    return scoredChunks
      .filter(chunk => chunk.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, k);
  };

  // 하이브리드 검색 (벡터 + 키워드)
  const performHybridSearch = (query, k = 5) => {
    const vectorResults = performVectorSearch(query, k);
    const keywordResults = performKeywordSearch(query, k);
    
    // 결과 합치기 및 중복 제거
    const combined = [...vectorResults, ...keywordResults];
    const unique = combined.filter((item, index, self) => 
      self.findIndex(t => t.id === item.id) === index
    );
    
    return unique.slice(0, k);
  };

  // 키워드 검색
  const performKeywordSearch = (query, k = 3) => {
    const allChunks = documentDatabase.flatMap(doc => doc.chunks || []);
    if (!allChunks.length) return [];

    const results = allChunks.filter(chunk => 
      chunk.content.toLowerCase().includes(query.toLowerCase())
    );

    return results.slice(0, k);
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    setIsBuilding(true);
    
    for (const file of files) {
      if (file.type === 'application/pdf' || file.type === 'text/plain' || file.name.endsWith('.txt')) {
        try {
          const base64Data = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
              const base64 = reader.result.split(",")[1];
              resolve(base64);
            };
            reader.onerror = () => reject(new Error("파일 읽기 실패"));
            reader.readAsDataURL(file);
          });

          const processedDoc = await processDocument({
            name: file.name,
            type: file.type,
            size: file.size,
            base64Data: base64Data
          });

          setUploadedFiles(prev => [...prev, processedDoc]);
          if (processedDoc.processed) {
            setDocumentDatabase(prev => [...prev, processedDoc]);
          }
        } catch (error) {
          console.error('파일 업로드 오류:', error);
          alert(`${file.name} 업로드에 실패했습니다.`);
        }
      } else {
        alert(`${file.name}: PDF 또는 텍스트 파일만 지원됩니다.`);
      }
    }
    
    setIsBuilding(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (indexToRemove) => {
    const fileToRemove = uploadedFiles[indexToRemove];
    setUploadedFiles(prev => prev.filter((_, index) => index !== indexToRemove));
    setDocumentDatabase(prev => prev.filter(doc => doc.name !== fileToRemove.name));
  };

  const performSearch = async (query) => {
    if (!query.trim()) return;

    let results = [];
    
    switch (searchMode) {
      case 'vector':
        results = performVectorSearch(query, 5);
        break;
      case 'keyword':
        results = performKeywordSearch(query, 5);
        break;
      case 'smart':
      default:
        results = performHybridSearch(query, 5);
        break;
    }
    
    setSearchResults(results);
  };

  const askQuestion = async () => {
    if (!currentQuestion.trim()) {
      alert('질문을 입력해주세요.');
      return;
    }

    if (uploadedFiles.length === 0) {
      alert('먼저 문서를 업로드해주세요.');
      return;
    }

    setIsLoading(true);
    
    const userMessage = { role: 'user', content: currentQuestion, timestamp: new Date() };
    setConversation(prev => [...prev, userMessage]);

    try {
      let contextContent = '';
      
      // 검색 모드에 따른 컨텍스트 구성
      if (searchMode === 'smart' || searchMode === 'vector' || searchMode === 'keyword') {
        // RAG 방식: 관련 청크 검색
        const relevantChunks = performHybridSearch(currentQuestion, 3);
        if (relevantChunks.length > 0) {
          contextContent = relevantChunks.map(chunk => 
            `[출처: ${chunk.source}] ${chunk.content}`
          ).join('\n\n');
        }
      }

      // 문서들을 Claude API에 전송할 형식으로 준비
      const documentContent = [];
      
      // PDF 문서들 추가
      uploadedFiles.filter(file => file.type === 'application/pdf').forEach(file => {
        documentContent.push({
          type: "document",
          source: {
            type: "base64",
            media_type: "application/pdf",
            data: file.base64Data,
          }
        });
      });

      // 텍스트 컨텍스트 추가 (RAG 검색 결과 또는 전체 텍스트)
      if (contextContent) {
        documentContent.push({
          type: "text",
          text: `관련 문서 내용:\n${contextContent}`
        });
      } else {
        // RAG 결과가 없으면 전체 텍스트 문서 추가
        uploadedFiles.filter(file => file.textContent).forEach(file => {
          documentContent.push({
            type: "text",
            text: `문서 "${file.name}"의 내용:\n${file.textContent}`
          });
        });
      }

      // 질문 추가
      documentContent.push({
        type: "text",
        text: `질문: ${currentQuestion}\n\n위 문서들을 기반으로 정확하고 자세한 답변을 해주세요. 답변의 근거가 되는 출처를 명시해주세요.`
      });

      const messages = [
        {
          role: "system",
          content: systemPrompt
        },
        {
          role: "user",
          content: documentContent
        }
      ];

      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 2000,
          temperature: temperature,
          messages: messages
        })
      });

      if (!response.ok) {
        throw new Error(`API 요청 실패: ${response.status}`);
      }

      const data = await response.json();
      const assistantResponse = data.content[0].text;

      const aiMessage = { 
        role: 'assistant', 
        content: assistantResponse, 
        timestamp: new Date(),
        searchMode: searchMode
      };
      
      setConversation(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('질문 처리 오류:', error);
      const errorMessage = { 
        role: 'assistant', 
        content: '죄송합니다. 질문 처리 중 오류가 발생했습니다. 다시 시도해주세요.', 
        timestamp: new Date(),
        isError: true
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setCurrentQuestion('');
    }
  };

  const clearConversation = () => {
    setConversation([]);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* 헤더 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">🧠 Advanced DocuQA</h1>
          <p className="text-gray-600">AI 기반 문서 분석 및 지능형 질의응답 시스템</p>
        </div>

        {/* 탭 네비게이션 */}
        <div className="bg-white rounded-lg shadow-lg mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-3 font-medium flex items-center ${
                activeTab === 'upload' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'
              }`}
            >
              <Upload className="mr-2" size={18} />
              문서 관리
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`px-6 py-3 font-medium flex items-center ${
                activeTab === 'search' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'
              }`}
            >
              <Search className="mr-2" size={18} />
              검색 & 분석
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-3 font-medium flex items-center ${
                activeTab === 'chat' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'
              }`}
            >
              <MessageCircle className="mr-2" size={18} />
              질의응답
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-6 py-3 font-medium flex items-center ${
                activeTab === 'settings' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'
              }`}
            >
              <Settings className="mr-2" size={18} />
              설정
            </button>
          </div>

          {/* 문서 업로드 탭 */}
          {activeTab === 'upload' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <FileText className="mr-2" size={20} />
                문서 업로드 & 데이터베이스 구축
              </h2>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors mb-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <FileText className="mx-auto mb-4 text-gray-400" size={48} />
                  <p className="text-gray-600 mb-2">클릭해서 파일을 선택하세요</p>
                  <p className="text-sm text-gray-500">PDF, TXT 파일 지원 • 자동 청킹 및 인덱싱</p>
                </label>
              </div>

              {isBuilding && (
                <div className="flex items-center justify-center py-4 text-blue-600">
                  <Loader2 className="animate-spin mr-2" size={20} />
                  문서 처리 및 데이터베이스 구축 중...
                </div>
              )}

              {/* 업로드된 파일 목록 */}
              {uploadedFiles.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2 flex items-center">
                    <Database className="mr-2" size={16} />
                    문서 데이터베이스 ({uploadedFiles.length}개)
                  </h3>
                  <div className="space-y-2">
                    {uploadedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                        <div className="flex items-center">
                          <FileText size={16} className="text-blue-500 mr-2" />
                          <div>
                            <span className="text-sm font-medium">{file.name}</span>
                            <div className="text-xs text-gray-500">
                              {formatFileSize(file.size)}
                              {file.chunks && ` • ${file.chunks.length} 청크`}
                              {file.processed ? ' • 처리완료' : ' • 실시간 처리'}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => removeFile(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 검색 & 분석 탭 */}
          {activeTab === 'search' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Brain className="mr-2" size={20} />
                지능형 문서 검색
              </h2>

              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium mb-2">검색 모드</label>
                  <select
                    value={searchMode}
                    onChange={(e) => setSearchMode(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="smart">🧠 스마트 검색 (하이브리드)</option>
                    <option value="vector">📊 벡터 유사도 검색</option>
                    <option value="keyword">🔍 키워드 검색</option>
                  </select>
                </div>
              </div>

              <div className="flex space-x-2 mb-4">
                <input
                  type="text"
                  value={currentQuestion}
                  onChange={(e) => setCurrentQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && performSearch(currentQuestion)}
                  placeholder="문서에서 검색할 내용을 입력하세요..."
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-2"
                />
                <button
                  onClick={() => performSearch(currentQuestion)}
                  className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 flex items-center"
                >
                  <Search size={20} />
                </button>
              </div>

              {/* 검색 결과 */}
              {searchResults.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">검색 결과 ({searchResults.length}개)</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {searchResults.map((result, index) => (
                      <div key={index} className="bg-gray-50 p-3 rounded border-l-4 border-blue-500">
                        <div className="text-xs text-blue-600 mb-1">📄 {result.source}</div>
                        <div className="text-sm">{result.content.substring(0, 200)}...</div>
                        {result.score && (
                          <div className="text-xs text-gray-500 mt-1">관련도: {result.score}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 질의응답 탭 */}
          {activeTab === 'chat' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold flex items-center">
                  <MessageCircle className="mr-2" size={20} />
                  AI 질의응답 ({searchMode === 'smart' ? '스마트' : searchMode === 'vector' ? '벡터' : '키워드'} 모드)
                </h2>
                {conversation.length > 0 && (
                  <button
                    onClick={clearConversation}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    대화 내역 지우기
                  </button>
                )}
              </div>

              {/* 대화 내역 */}
              <div className="h-96 overflow-y-auto mb-4 p-4 bg-gray-50 rounded-lg">
                {conversation.length === 0 ? (
                  <div className="text-center text-gray-500 mt-20">
                    <BookOpen className="mx-auto mb-4 text-gray-400" size={48} />
                    문서를 업로드한 후 질문을 시작해보세요!
                    <div className="text-sm mt-2">현재 검색 모드: {searchMode}</div>
                  </div>
                ) : (
                  conversation.map((message, index) => (
                    <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className={`inline-block max-w-xs lg:max-w-2xl px-4 py-2 rounded-lg ${
                        message.role === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : message.isError 
                            ? 'bg-red-100 text-red-800'
                            : 'bg-white text-gray-800 shadow'
                      }`}>
                        <p className="whitespace-pre-wrap">{message.content}</p>
                        <p className="text-xs mt-1 opacity-70">
                          {message.timestamp.toLocaleTimeString()}
                          {message.searchMode && ` • ${message.searchMode} 모드`}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* 질문 입력 */}
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={currentQuestion}
                  onChange={(e) => setCurrentQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isLoading && askQuestion()}
                  placeholder="문서에 대해 질문해보세요..."
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading || uploadedFiles.length === 0}
                />
                <button
                  onClick={askQuestion}
                  disabled={isLoading || !currentQuestion.trim() || uploadedFiles.length === 0}
                  className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 flex items-center"
                >
                  {isLoading ? (
                    <Loader2 className="animate-spin" size={20} />
                  ) : (
                    <Send size={20} />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* 설정 탭 */}
          {activeTab === 'settings' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Settings className="mr-2" size={20} />
                AI 엔진 설정
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">시스템 프롬프트</label>
                  <textarea
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    rows={4}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="AI의 역할과 답변 스타일을 정의하세요..."
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    예: "당신은 사주명리 전문가입니다..." 또는 "당신은 법률 전문가입니다..."
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Temperature (창의성): {temperature}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    낮음 (0.0) = 일관된 답변 • 높음 (1.0) = 창의적 답변
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">현재 설정 요약</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• 모델: Claude Sonnet 4</li>
                    <li>• 검색 모드: {searchMode}</li>
                    <li>• Temperature: {temperature}</li>
                    <li>• 업로드된 문서: {uploadedFiles.length}개</li>
                    <li>• 처리된 청크: {documentDatabase.reduce((acc, doc) => acc + (doc.chunks?.length || 0), 0)}개</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 사용법 안내 */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">🚀 Advanced DocuQA 기능</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-700">
            <div>
              <h4 className="font-semibold mb-1">📄 문서 처리</h4>
              <ul className="space-y-1">
                <li>• PDF 및 텍스트 파일 지원</li>
                <li>• 자동 청킹 및 인덱싱</li>
                <li>• 메타데이터 추출</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-1">🧠 검색 엔진</h4>
              <ul className="space-y-1">
                <li>• 벡터 유사도 검색</li>
                <li>• 키워드 검색</li>
                <li>• 하이브리드 스마트 검색</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocuQAApp;