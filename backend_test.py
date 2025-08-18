#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import os
import tempfile

class SubFlixAPITester:
    def __init__(self, base_url="https://subflix-burner.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_settings_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def run_api_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return self.log_test(name, False, f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json() if response.content else {}
                    return self.log_test(name, True, f"Status: {response.status_code}"), response_data
                except:
                    return self.log_test(name, True, f"Status: {response.status_code}"), {}
            else:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = f" - {error_data.get('detail', 'No detail')}"
                except:
                    error_detail = f" - Response: {response.text[:100]}"
                
                return self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}{error_detail}"), {}

        except requests.exceptions.RequestException as e:
            return self.log_test(name, False, f"Request error: {str(e)}"), {}
        except Exception as e:
            return self.log_test(name, False, f"Unexpected error: {str(e)}"), {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        print("\n🔍 Testing Root API Endpoint...")
        success, data = self.run_api_test("Root API", "GET", "", 200)
        if success and data.get("message"):
            print(f"   API Message: {data['message']}")
        return success

    def test_settings_endpoints(self):
        """Test settings GET and PUT endpoints"""
        print("\n🔍 Testing Settings Endpoints...")
        
        # Test GET settings
        success, settings_data = self.run_api_test("GET Settings", "GET", "settings", 200)
        if success:
            print(f"   Settings loaded with ID: {settings_data.get('id', 'No ID')}")
            self.test_settings_id = settings_data.get('id')
        
        # Test PUT settings with sample data
        test_settings = {
            "movies_source_path": "/test/movies",
            "movies_output_path": "/test/output/movies",
            "tvshows_source_path": "/test/tvshows", 
            "tvshows_output_path": "/test/output/tvshows",
            "bunnycdn_api_key": "test_api_key",
            "bunnycdn_storage_zone": "test_zone",
            "bunnycdn_base_url": "https://test.b-cdn.net",
            "bunnycdn_service_type": "storage"
        }
        
        success, updated_data = self.run_api_test("PUT Settings", "PUT", "settings", 200, test_settings)
        if success:
            print(f"   Settings updated successfully")
            # Verify the update worked
            success2, verify_data = self.run_api_test("Verify Settings Update", "GET", "settings", 200)
            if success2 and verify_data.get('movies_source_path') == test_settings['movies_source_path']:
                print(f"   ✅ Settings persistence verified")
            else:
                print(f"   ❌ Settings persistence failed")
        
        return success

    def test_scan_endpoints(self):
        """Test scan endpoints for movies and TV shows"""
        print("\n🔍 Testing Scan Endpoints...")
        
        # Test scan movies (will fail if no folder exists, but should return proper error)
        success1, scan_data1 = self.run_api_test("Scan Movies", "POST", "scan", 400, {"content_type": "movies"})
        if not success1:
            # Try with 400 status as expected when no folder exists
            success1, scan_data1 = self.run_api_test("Scan Movies (No Folder)", "POST", "scan", 400, {"content_type": "movies"})
        
        # Test scan TV shows
        success2, scan_data2 = self.run_api_test("Scan TV Shows", "POST", "scan", 400, {"content_type": "tvshows"})
        if not success2:
            success2, scan_data2 = self.run_api_test("Scan TV Shows (No Folder)", "POST", "scan", 400, {"content_type": "tvshows"})
        
        # Test invalid content type
        success3, _ = self.run_api_test("Scan Invalid Type", "POST", "scan", 400, {"content_type": "invalid"})
        
        return success1 or success2  # At least one should work or fail properly

    def test_video_files_endpoints(self):
        """Test video files endpoints"""
        print("\n🔍 Testing Video Files Endpoints...")
        
        # Test GET video files
        success1, files_data = self.run_api_test("GET Video Files", "GET", "video-files", 200)
        if success1:
            print(f"   Found {len(files_data)} video files")
        
        # Test GET video files with content type filter
        success2, movies_data = self.run_api_test("GET Movies Only", "GET", "video-files", 200, params={"content_type": "movies"})
        success3, tv_data = self.run_api_test("GET TV Shows Only", "GET", "video-files", 200, params={"content_type": "tvshows"})
        
        # Test clear video files
        success4, _ = self.run_api_test("Clear Video Files", "DELETE", "video-files", 200)
        
        return success1 and success2 and success3 and success4

    def test_jobs_endpoints(self):
        """Test processing jobs endpoints"""
        print("\n🔍 Testing Jobs Endpoints...")
        
        # Test GET jobs
        success1, jobs_data = self.run_api_test("GET Jobs", "GET", "jobs", 200)
        if success1:
            print(f"   Found {len(jobs_data)} processing jobs")
        
        # Test clear jobs
        success2, _ = self.run_api_test("Clear Jobs", "DELETE", "jobs", 200)
        
        # Test process video (should fail with 404 since no video exists)
        success3, _ = self.run_api_test("Process Non-existent Video", "POST", "process/fake-id", 404)
        
        # Test get job status (should fail with 404)
        success4, _ = self.run_api_test("Get Non-existent Job", "GET", "jobs/fake-id", 404)
        
        return success1 and success2 and success3 and success4

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🔍 Testing Error Handling...")
        
        # Test scan without settings configured (reset settings first)
        empty_settings = {
            "movies_source_path": "",
            "movies_output_path": "",
            "tvshows_source_path": "",
            "tvshows_output_path": ""
        }
        
        self.run_api_test("Reset Settings", "PUT", "settings", 200, empty_settings)
        
        # Now scan should fail with proper error
        success1, _ = self.run_api_test("Scan Without Config", "POST", "scan", 400, {"content_type": "movies"})
        
        # Test invalid endpoints
        success2, _ = self.run_api_test("Invalid Endpoint", "GET", "nonexistent", 404)
        
        return success1 and success2

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting SubFlix API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Test basic connectivity
        try:
            response = requests.get(self.base_url, timeout=5)
            print(f"✅ Base URL accessible (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return False
        
        # Run all test suites
        test_results = []
        test_results.append(self.test_root_endpoint())
        test_results.append(self.test_settings_endpoints())
        test_results.append(self.test_scan_endpoints())
        test_results.append(self.test_video_files_endpoints())
        test_results.append(self.test_jobs_endpoints())
        test_results.append(self.test_error_handling())
        
        # Print summary
        print(f"\n📊 Test Results Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test execution"""
    tester = SubFlixAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())