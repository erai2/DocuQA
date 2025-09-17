import React, { useState, useRef } from 'react';
import { FileText, Upload, MessageCircle, Send, Loader2, X } from 'lucide-react';

const DocuQAApp = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    
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

          setUploadedFiles(prev => [...prev, {
            name: file.name,
            type: file.type,
            size: file.size,
            base64Data: base64Data
          }]);
        } catch (error) {
          console.error('파일 업로드 오류:', error);
          alert(`${file.name} 업로드에 실패했습니다.`);
        }
      } else {
        alert(`${file.name}: PDF 또는 텍스트 파일만 지원됩니다.`);
      }
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (indexToRemove) => {
    setUploadedFiles(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  const askQuestion = async () => {
    if (!currentQuestion.trim() || uploadedFiles.length === 0) {
      alert(uploadedFiles.length === 0 ? '먼저 문서를 업로드해주세요.' : '질문을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    
    const userMessage = { role: 'user', content: currentQuestion, timestamp: new Date() };
    setConversation(prev => [...prev, userMessage]);

    try {
      // 문서들을 Claude API에 전송할 형식으로 준비
      const documentContent = uploadedFiles.map(file => {
        if (file.type === 'application/pdf') {
          return {
            type: "document",
            source: {
              type: "base64",
              media_type: "application/pdf",
              data: file.base64Data,
            }
          };
        } else {
          // 텍스트 파일의 경우 base64를 디코드해서 텍스트로 변환
          const textContent = atob(file.base64Data);
          return {
            type: "text",
            text: `문서 "${file.name}"의 내용:\n${textContent}`
          };
        }
      });

      const messages = [
        {
          role: "user",
          content: [
            ...documentContent,
            {
              type: "text",
              text: `업로드된 문서들을 기반으로 다음 질문에 답해주세요:\n\n${currentQuestion}\n\n답변은 한국어로, 문서의 내용을 근거로 하여 정확하고 자세하게 해주세요. 만약 문서에서 답을 찾을 수 없다면 그렇게 말해주세요.`
            }
          ]
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
        timestamp: new Date() 
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
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">📄 DocuQA</h1>
          <p className="text-gray-600">문서를 업로드하고 AI에게 질문해보세요</p>
        </div>

        {/* 파일 업로드 영역 */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Upload className="mr-2" size={20} />
            문서 업로드
          </h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
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
              <p className="text-gray-600 mb-2">클릭해서 파일을 선택하거나 여기로 드래그하세요</p>
              <p className="text-sm text-gray-500">PDF, TXT 파일 지원</p>
            </label>
          </div>

          {/* 업로드된 파일 목록 */}
          {uploadedFiles.length > 0 && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">업로드된 파일 ({uploadedFiles.length}개)</h3>
              <div className="space-y-2">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                    <div className="flex items-center">
                      <FileText size={16} className="text-blue-500 mr-2" />
                      <span className="text-sm font-medium">{file.name}</span>
                      <span className="text-xs text-gray-500 ml-2">({formatFileSize(file.size)})</span>
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

        {/* 대화 영역 */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <MessageCircle className="mr-2" size={20} />
              질의응답
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
                문서를 업로드한 후 질문을 시작해보세요!
              </div>
            ) : (
              conversation.map((message, index) => (
                <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                  <div className={`inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.role === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : message.isError 
                        ? 'bg-red-100 text-red-800'
                        : 'bg-white text-gray-800 shadow'
                  }`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
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

        {/* 사용법 안내 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">사용법</h3>
          <ol className="text-sm text-blue-700 space-y-1">
            <li>1. PDF 또는 텍스트 파일을 업로드하세요</li>
            <li>2. 문서 내용에 대해 질문을 입력하세요</li>
            <li>3. AI가 문서를 분석하여 답변해드립니다</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default DocuQAApp;