<?php
  set_time_limit(300);
  
  class DCAT{
      var $url;
      var $username;
      var $password;
      var $names;
      var $datasets;
      var $themas;
      var $categorien;
      var $token;
      var $curl_opts;
           
      function DCAT($url = DCAT_URL, $username = DCAT_USER, $password = DCAT_PASSWORD){
          $this->url = $url;
          $this->username = $username;
          $this->password = $password;
          $this->curl_opts = array(
            CURLOPT_RETURNTRANSFER => 1,
            CURLOPT_SSL_VERIFYPEER => false,
          );
          $proxy = getenv('HTTPS_PROXY');
          if($proxy) {
              $this->curl_opts[CURLOPT_PROXY] = $proxy;
          }
          $this->setToken();
      }
      
      function setToken(){
        if(stripos($this->url,"acc") > 0){
            $auth_url = "https://acc.api.data.amsterdam.nl/oauth2/authorize";
            $redirect_url = "https://acc.data.amsterdam.nl/";
        } else {
            $auth_url = "https://api.data.amsterdam.nl/oauth2/authorize";
            $redirect_url = "https://data.amsterdam.nl/";            
        }

        $data = [
          'idp_id' => 'datapunt',
          'response_type'=> 'token',
          'client_id' => 'citydata',
          'scope' => 'CAT/R CAT/W',
          'state' => randomword(10),
          'redirect_uri' => $redirect_url
        ];

        $request_url = $auth_url . "?" . http_build_query($data);
        //print($request_url);
        
        $curl = curl_init();
        curl_setopt_array($curl, $this->curl_opts + array(
            CURLOPT_HEADER => true,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_URL => $request_url
        ));
        
        $resp = curl_exec($curl);
        if($resp === false) {
            throw new Exception('Curl error: ' . curl_error($curl));
        }

        $headers = get_headers_from_curl_response($resp);
        // print("Headers:");
        // print_r($headers);
        $location = $headers["Location"] ? $headers["Location"] : curl_getinfo($curl)['redirect_url'];
        // print("Location: $location\n");
        if(!$location) {
            throw new Exception('Redirect location not found!');
        }
        curl_close($curl);

        $data = [
            "type" => "employee_plus",
            "email" => $this->username,
            "password" => $this->password        ];
        
        $data = http_build_query($data);
        
        $curl  = curl_init();
        curl_setopt_array( $curl ,  $this->curl_opts +  array (
            CURLOPT_HEADER => true,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $data,
            CURLOPT_URL => $location
        ));
        $response  = curl_exec( $curl );
        if($response === false) {
            throw new Exception('Curl error: ' . curl_error($curl));
        }

        $headers = get_headers_from_curl_response($response);

        $location = $headers["Location"] ? $headers["Location"] : curl_getinfo($curl)['redirect_url'];
        if(!$location) {
            throw new Exception('Redirect location not found!');
        }
        curl_close( $curl );

        $curl = curl_init();
        curl_setopt_array($curl, $this->curl_opts + array(
            CURLOPT_HEADER => true,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_URL => $location
        ));
        
        $resp = curl_exec($curl);
        if($resp === false) {
            throw new Exception('Curl error: ' . curl_error($curl));
        }

        $headers = get_headers_from_curl_response($resp);

        $info = curl_getinfo($curl);
        print("Info:");
        print_r($info);
        print("Headers:");
        print_r($headers);

        $location = $headers["Location"] ? $headers["Location"] : $info['redirect_url'];
        if(!$location) {
            throw new Exception('Redirect location not found!');
        }
        curl_close($curl);

        $params = explode("#",$location);
        parse_str($params[1], $arr);
        
        $this->token = $arr["access_token"];
        if( ! $this->token ) {
            throw new Exception("Unable to login. Token not defined");
        }
        // print("Token set to: ". $this->token);
      }
      
      
      function getDatasets(){
        $url = $this->url . "harvest";
        $curl = curl_init();
        curl_setopt_array($curl, $this->curl_opts + array(
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_HTTPHEADER => array("Authorization: Bearer ". $this->token),
            CURLOPT_URL => $url
        ));
        
        $resp = curl_exec($curl);
        if($resp === false) {
            throw new Exception('Curl error: ' . curl_error($curl));
        }
        curl_close($curl);

        $this->harvest = json_decode($resp);

        $param_dataset = "dcat:dataset";
        $param_id = "@id";
        foreach($this->harvest->$param_dataset as $result){
            $this->datasets[$result->$param_id] = $result;
        }
      }
      
    function putSet($set){
        $param_identifier = "dct:identifier";
        $url = $this->url ."datasets/". $set->$param_identifier;
        
        //Get eTag
        $headers = get_headers($url,1);
        //print_r($headers);
        $etag = $headers["Etag"]; 
        
        $data = json_encode($set);
        $curl = curl_init();
        curl_setopt_array( $curl ,  $this->curl_opts +  array (
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_HTTPHEADER => array('Content-Type: application/json',"Authorization: Bearer ". $this->token,"If-Match: ".$etag),
            CURLOPT_POST => true,
            CURLOPT_CUSTOMREQUEST => "PUT",
            CURLOPT_POSTFIELDS => $data,
            CURLOPT_URL => $url
        ));
        $response  = curl_exec( $curl );
        if(!curl_errno($curl)){
          $info = curl_getinfo($curl); 
          //echo 'Took ' . $info['total_time'] . ' seconds to send a request to ' . $info['url']; 
          //print("<PRE>");print_r($info);print("</PRE>");
        } else { 
          echo 'Curl error: ' . curl_error($curl); 
        } 
        curl_close( $curl );
    }

    function postSet($set){
        $url = $this->url ."datasets";
        $data = json_encode($set);
        
        $curl = curl_init();
        curl_setopt_array( $curl ,  $this->curl_opts + array (
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_HTTPHEADER => array('Content-Type: application/json',"Authorization: Bearer ". $this->token),
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $data,
            CURLOPT_URL => $url
        ));
        $response  = curl_exec( $curl );
        if(!curl_errno($curl)){ 
          $info = curl_getinfo($curl); 
          //echo 'Took ' . $info['total_time'] . ' seconds to send a request to ' . $info['url']; 
          //print("<PRE>");print_r($info);print("</PRE>");
        } else { 
          echo 'Curl error: ' . curl_error($curl); 
        } 
        curl_close( $curl );
    }
  }
  
//standard functions. Should be placed somewhere else...
function randomword($aantal){
    $result = "";
    $word = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for($i = 0; $i < $aantal; $i++){
        $result .= $word[rand(0,61)];
    }
    return $result;
}

function get_headers_from_curl_response($response)
{
    $headers = array();
    $header_text = substr($response, 0, strpos($response, "\r\n\r\n"));

    foreach (explode("\r\n", $header_text) as $i => $line)
        if ($i === 0)
            $headers['http_code'] = $line;
        else
        {
            list ($key, $value) = explode(': ', $line);
            $headers[$key] = $value;
        }
    return $headers;
}
?>