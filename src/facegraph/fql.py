# -*- coding: utf-8 -*-

import urllib2

import bunch
import simplejson as json
from graph import GraphException
from url_operations import add_path, update_query_params

class FQL(object):
    
    """
    A maker of single and multiple FQL queries.
    
    Usage
    =====
    
    Single queries:
    
        >>> q = FQL('access_token')
        >>> result = q("SELECT post_id FROM stream WHERE source_id = ...")
        >>> result
        [Bunch(post_id='XXXYYYZZZ'), ...]
        
        >>> result[0]
        Bunch(post_id='XXXYYYZZZ')
        
        >>> result[0].post_id
        'XXXYYYZZZ'
    
    Multiple queries:
    
        >>> q = FQL('access_token')
        >>> result = q.multi(dict(query1="SELECT...", query2="SELECT..."))
        
        >>> result[0].name
        'query1'
        >>> result[0].fql_result_set
        [...]
        
        >>> result[1].name
        'query2'
        >>> result[1].fql_result_set
        [...]
    
    """
    
    ENDPOINT = 'https://api.facebook.com/method/'
    
    def __init__(self, access_token=None, err_handler=None):
        self.access_token = access_token
        self.err_handler = err_handler
    
    def __call__(self, query, **params):
        
        """
        Execute a single FQL query (using `fql.query`).
        
        Example:
        
            >>> q = FQL('access_token')
            >>> result = q("SELECT post_id FROM stream WHERE source_id = ...")
            >>> result
            [Bunch(post_id='XXXYYYZZZ'), ...]
            
            >>> result[0]
            Bunch(post_id='XXXYYYZZZ')
            
            >>> result[0].post_id
            'XXXYYYZZZ'
        
        """
        
        url = add_path(self.ENDPOINT, 'fql.query')
        params.update(query=query, access_token=self.access_token,
                      format='json')
        url = update_query_params(url, params)
        
        return self.fetch_json(url)
    
    def multi(self, queries, **params):
        
        """
        Execute multiple FQL queries (using `fql.multiquery`).
        
        Example:
        
            >>> q = FQL('access_token')
            >>> result = q.multi(dict(query1="SELECT...", query2="SELECT..."))
            
            >>> result[0].name
            'query1'
            >>> result[0].fql_result_set
            [...]
            
            >>> result[1].name
            'query2'
            >>> result[1].fql_result_set
            [...]
        
        """
        
        url = add_path(self.ENDPOINT, 'fql.multiquery')
        params.update(queries=json.dumps(queries),
                      access_token=self.access_token, format='json')
        url = update_query_params(url, params)
        
        return self.fetch_json(url)
    
    @classmethod
    def fetch_json(cls, url, data=None):
        response = json.loads(cls.fetch(url, data=data))
        if isinstance(response, dict):
            if response.get("error_msg"):
                code = response.get("error_code")
                msg = response.get("error_msg")
                args = response.get("request_args")
                raise GraphException(code, msg, args=args)
        return bunch.bunchify(response)
    
    @staticmethod
    def fetch(url, data=None):
        conn = urllib2.urlopen(url, data=data)
        try:
            return conn.read()
        finally:
            conn.close()
