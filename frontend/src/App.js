import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Separator } from "./components/ui/separator";
import { 
  Settings, 
  Film, 
  Tv, 
  Play, 
  Check, 
  X, 
  Clock, 
  Upload, 
  Folder,
  FileVideo,
  Subtitles
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [settings, setSettings] = useState({});
  const [videoFiles, setVideoFiles] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanningType, setScanningType] = useState("");
  
  // Load initial data
  useEffect(() => {
    loadSettings();
    loadVideoFiles();
    loadJobs();
  }, []);
  
  // Auto-refresh jobs every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (activeTab === "jobs") {
        loadJobs();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error("Error loading settings:", error);
    }
  };

  const loadVideoFiles = async () => {
    try {
      const response = await axios.get(`${API}/video-files`);
      setVideoFiles(response.data);
    } catch (error) {
      console.error("Error loading video files:", error);
    }
  };

  const loadJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error("Error loading jobs:", error);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      await axios.put(`${API}/settings`, settings);
      alert("Settings saved successfully!");
    } catch (error) {
      console.error("Error saving settings:", error);
      alert("Error saving settings");
    } finally {
      setLoading(false);
    }
  };

  const scanFolders = async (contentType) => {
    try {
      setLoading(true);
      setScanningType(contentType);
      const response = await axios.post(`${API}/scan`, {
        content_type: contentType
      });
      alert(`Scanned ${response.data.scanned_files} files`);
      await loadVideoFiles();
    } catch (error) {
      console.error("Error scanning folders:", error);
      alert("Error scanning folders");
    } finally {
      setLoading(false);
      setScanningType("");
    }
  };

  const processVideo = async (videoFileId) => {
    try {
      setLoading(true);
      await axios.post(`${API}/process/${videoFileId}`);
      alert("Processing started!");
      await loadVideoFiles();
      await loadJobs();
    } catch (error) {
      console.error("Error starting processing:", error);
      alert("Error starting processing");
    } finally {
      setLoading(false);
    }
  };

  const clearVideoFiles = async () => {
    if (window.confirm("Are you sure you want to clear all video files?")) {
      try {
        await axios.delete(`${API}/video-files`);
        await loadVideoFiles();
      } catch (error) {
        console.error("Error clearing video files:", error);
      }
    }
  };

  const clearJobs = async () => {
    if (window.confirm("Are you sure you want to clear all jobs?")) {
      try {
        await axios.delete(`${API}/jobs`);
        await loadJobs();
      } catch (error) {
        console.error("Error clearing jobs:", error);
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "completed": return "bg-green-500";
      case "processing": return "bg-blue-500";
      case "failed": return "bg-red-500";
      case "queued": return "bg-yellow-500";
      default: return "bg-gray-500";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed": return <Check className="w-4 h-4" />;
      case "processing": return <Clock className="w-4 h-4 animate-spin" />;
      case "failed": return <X className="w-4 h-4" />;
      case "queued": return <Clock className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const movieFiles = videoFiles.filter(f => f.content_type === "movies");
  const tvFiles = videoFiles.filter(f => f.content_type === "tvshows");
  const filesWithSubtitles = videoFiles.filter(f => f.subtitle_path);
  const completedFiles = videoFiles.filter(f => f.status === "completed");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Subtitles className="w-8 h-8 text-blue-500" />
              <h1 className="text-2xl font-bold text-white">SubFlix</h1>
            </div>
            <Badge variant="secondary" className="bg-blue-500/20 text-blue-400">
              Subtitle Embedding Tool
            </Badge>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-gray-900">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-blue-600">
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="library" className="data-[state=active]:bg-blue-600">
              Library
            </TabsTrigger>
            <TabsTrigger value="jobs" className="data-[state=active]:bg-blue-600">
              Jobs
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-blue-600">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
                  <FileVideo className="h-4 w-4 text-gray-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{videoFiles.length}</div>
                  <p className="text-xs text-gray-400">
                    {movieFiles.length} movies, {tvFiles.length} TV shows
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">With Subtitles</CardTitle>
                  <Subtitles className="h-4 w-4 text-blue-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-400">{filesWithSubtitles.length}</div>
                  <p className="text-xs text-gray-400">
                    Ready for processing
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Processed</CardTitle>
                  <Check className="h-4 w-4 text-green-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-400">{completedFiles.length}</div>
                  <p className="text-xs text-gray-400">
                    Successfully embedded
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
                  <Clock className="h-4 w-4 text-yellow-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-yellow-400">
                    {jobs.filter(j => j.status === "processing" || j.status === "queued").length}
                  </div>
                  <p className="text-xs text-gray-400">
                    In queue or processing
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="bg-gray-900 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-300 flex items-center">
                      <Film className="w-4 h-4 mr-2" />
                      Scan Movies
                    </h3>
                    <Button
                      onClick={() => scanFolders("movies")}
                      disabled={loading || scanningType === "movies"}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      {scanningType === "movies" ? "Scanning..." : "Scan Movies Folder"}
                    </Button>
                  </div>
                  
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-300 flex items-center">
                      <Tv className="w-4 h-4 mr-2" />
                      Scan TV Shows
                    </h3>
                    <Button
                      onClick={() => scanFolders("tvshows")}
                      disabled={loading || scanningType === "tvshows"}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      {scanningType === "tvshows" ? "Scanning..." : "Scan TV Shows Folder"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Library Tab */}
          <TabsContent value="library" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white">Video Library</h2>
              <Button 
                onClick={clearVideoFiles} 
                variant="destructive"
                size="sm"
              >
                Clear All
              </Button>
            </div>

            {videoFiles.length === 0 ? (
              <Card className="bg-gray-900 border-gray-700">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Folder className="w-12 h-12 text-gray-400 mb-4" />
                  <p className="text-gray-400 text-center">
                    No video files found. Use the scan feature to discover videos with subtitles.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {videoFiles.map((file) => (
                  <Card key={file.id} className="bg-gray-900 border-gray-700">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3">
                            {file.content_type === "movies" ? (
                              <Film className="w-5 h-5 text-blue-400" />
                            ) : (
                              <Tv className="w-5 h-5 text-green-400" />
                            )}
                            <div>
                              <h3 className="text-lg font-medium text-white truncate">
                                {file.file_name}
                              </h3>
                              <p className="text-sm text-gray-400">
                                {formatFileSize(file.file_size)} • {file.content_type}
                              </p>
                            </div>
                          </div>
                          
                          <div className="mt-2 flex items-center space-x-4">
                            <Badge className={`${getStatusColor(file.status)} text-white`}>
                              <span className="flex items-center space-x-1">
                                {getStatusIcon(file.status)}
                                <span>{file.status}</span>
                              </span>
                            </Badge>
                            
                            {file.subtitle_path && (
                              <Badge variant="secondary" className="bg-green-500/20 text-green-400">
                                <Subtitles className="w-3 h-3 mr-1" />
                                {file.subtitle_language} subtitle
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          {file.subtitle_path && file.status === "pending" && (
                            <Button
                              onClick={() => processVideo(file.id)}
                              disabled={loading}
                              className="bg-blue-600 hover:bg-blue-700"
                            >
                              <Play className="w-4 h-4 mr-1" />
                              Process
                            </Button>
                          )}
                          
                          {!file.subtitle_path && (
                            <Badge variant="destructive">
                              No subtitles
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Jobs Tab */}
          <TabsContent value="jobs" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white">Processing Jobs</h2>
              <Button 
                onClick={clearJobs} 
                variant="destructive"
                size="sm"
              >
                Clear All
              </Button>
            </div>

            {jobs.length === 0 ? (
              <Card className="bg-gray-900 border-gray-700">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Clock className="w-12 h-12 text-gray-400 mb-4" />
                  <p className="text-gray-400 text-center">
                    No processing jobs found. Start processing videos to see jobs here.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {jobs.map((job) => (
                  <Card key={job.id} className="bg-gray-900 border-gray-700">
                    <CardContent className="p-6">
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <Badge className={`${getStatusColor(job.status)} text-white`}>
                              <span className="flex items-center space-x-1">
                                {getStatusIcon(job.status)}
                                <span>{job.status}</span>
                              </span>
                            </Badge>
                            <h3 className="text-lg font-medium text-white">
                              {job.input_video_path.split('/').pop()}
                            </h3>
                          </div>
                          
                          {job.status === "processing" && (
                            <div className="text-sm text-blue-400">
                              {job.progress}%
                            </div>
                          )}
                        </div>
                        
                        {job.status === "processing" && (
                          <Progress 
                            value={job.progress} 
                            className="w-full bg-gray-700"
                          />
                        )}
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-gray-400">Input Video:</p>
                            <p className="text-gray-200 truncate">{job.input_video_path}</p>
                          </div>
                          <div>
                            <p className="text-gray-400">Output Path:</p>
                            <p className="text-gray-200 truncate">{job.output_path}</p>
                          </div>
                        </div>
                        
                        {job.error_message && (
                          <Alert className="border-red-500 bg-red-500/10">
                            <X className="h-4 w-4" />
                            <AlertDescription className="text-red-400">
                              {job.error_message}
                            </AlertDescription>
                          </Alert>
                        )}
                        
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>Created: {new Date(job.created_at).toLocaleString()}</span>
                          {job.completed_at && (
                            <span>Completed: {new Date(job.completed_at).toLocaleString()}</span>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Settings</h2>

            {/* Folder Configuration */}
            <Card className="bg-gray-900 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Folder className="w-5 h-5 mr-2" />
                  Folder Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-200 flex items-center">
                      <Film className="w-5 h-5 mr-2 text-blue-400" />
                      Movies
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <Label htmlFor="movies-source" className="text-gray-300">
                          Source Folder
                        </Label>
                        <Input
                          id="movies-source"
                          placeholder="/path/to/movies"
                          value={settings.movies_source_path || ""}
                          onChange={(e) => setSettings({...settings, movies_source_path: e.target.value})}
                          className="bg-gray-800 border-gray-600 text-white"
                        />
                      </div>
                      <div>
                        <Label htmlFor="movies-output" className="text-gray-300">
                          Output Folder
                        </Label>
                        <Input
                          id="movies-output"
                          placeholder="/path/to/processed/movies"
                          value={settings.movies_output_path || ""}
                          onChange={(e) => setSettings({...settings, movies_output_path: e.target.value})}
                          className="bg-gray-800 border-gray-600 text-white"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-200 flex items-center">
                      <Tv className="w-5 h-5 mr-2 text-green-400" />
                      TV Shows
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <Label htmlFor="tv-source" className="text-gray-300">
                          Source Folder
                        </Label>
                        <Input
                          id="tv-source"
                          placeholder="/path/to/tvshows"
                          value={settings.tvshows_source_path || ""}
                          onChange={(e) => setSettings({...settings, tvshows_source_path: e.target.value})}
                          className="bg-gray-800 border-gray-600 text-white"
                        />
                      </div>
                      <div>
                        <Label htmlFor="tv-output" className="text-gray-300">
                          Output Folder
                        </Label>
                        <Input
                          id="tv-output"
                          placeholder="/path/to/processed/tvshows"
                          value={settings.tvshows_output_path || ""}
                          onChange={(e) => setSettings({...settings, tvshows_output_path: e.target.value})}
                          className="bg-gray-800 border-gray-600 text-white"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* BunnyCDN Configuration */}
            <Card className="bg-gray-900 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Upload className="w-5 h-5 mr-2" />
                  BunnyCDN Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="bunnycdn-key" className="text-gray-300">
                      API Key
                    </Label>
                    <Input
                      id="bunnycdn-key"
                      type="password"
                      placeholder="Your BunnyCDN API Key"
                      value={settings.bunnycdn_api_key || ""}
                      onChange={(e) => setSettings({...settings, bunnycdn_api_key: e.target.value})}
                      className="bg-gray-800 border-gray-600 text-white"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="bunnycdn-zone" className="text-gray-300">
                      Storage Zone
                    </Label>
                    <Input
                      id="bunnycdn-zone"
                      placeholder="your-storage-zone"
                      value={settings.bunnycdn_storage_zone || ""}
                      onChange={(e) => setSettings({...settings, bunnycdn_storage_zone: e.target.value})}
                      className="bg-gray-800 border-gray-600 text-white"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="bunnycdn-url" className="text-gray-300">
                      Base URL
                    </Label>
                    <Input
                      id="bunnycdn-url"
                      placeholder="https://your-zone.b-cdn.net"
                      value={settings.bunnycdn_base_url || ""}
                      onChange={(e) => setSettings({...settings, bunnycdn_base_url: e.target.value})}
                      className="bg-gray-800 border-gray-600 text-white"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="bunnycdn-type" className="text-gray-300">
                      Service Type
                    </Label>
                    <Select 
                      value={settings.bunnycdn_service_type || "storage"}
                      onValueChange={(value) => setSettings({...settings, bunnycdn_service_type: value})}
                    >
                      <SelectTrigger className="bg-gray-800 border-gray-600 text-white">
                        <SelectValue placeholder="Select service type" />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-600">
                        <SelectItem value="storage">Storage</SelectItem>
                        <SelectItem value="stream">Stream</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button
                onClick={saveSettings}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? "Saving..." : "Save Settings"}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;