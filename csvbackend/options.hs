module Options(cmdlineOpts, Flag) where

import System.Console.GetOpt
import System.Environment
import Data.Maybe ( fromMaybe )

data Flag 
 = Socket String
   deriving Show

options :: [OptDescr Flag]
options =
 [ 
 , Option ['s'] ["socket"] (OptArg sock "FILE") "socket FILE"
 ]

sock :: Maybe String -> Flag
sock = Socket . fromMaybe "/tmp/csvbackend.sock"

cmdlineOpts :: IO [Flag]
cmdlineOpts = do
   argv <- getArgs :: IO [String]
   return case getOpt Permute options argv of
      (o,_,[]  ) -> return o
      (_,_,errs) -> ioError (userError (concat errs ++ usageInfo header options))
  where header = "Usage: csvbackend [OPTION...]"
