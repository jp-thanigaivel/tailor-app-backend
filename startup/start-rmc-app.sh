setEnv() {
        echo -e "INFO : Setting Environment"
        APP_NAME="rmc"
        APP_VENV="rmc_virtual_env/bin/activate"
        WEB_APP_HOME="/app/server/web-apps/rmc-app"
        APP_LOG=$WEB_APP_HOME"/logs/start.log"
        APP_WORKER=2
        APP_WORKER_CLASS="uvicorn.workers.UvicornWorker"
        APP_WORKER_TIMEOUT=60
        APP_BIND="0.0.0.0:6002"
        APP_ERROR_LOG_LEVEL="debug"
        APP_ACCESS_LOG=$WEB_APP_HOME"/logs/access-rmc.log"
        APP_ERROR_LOG=$WEB_APP_HOME"/logs/access-rmc.log"
}


getPID() {
        echo -e "INFO : Checking Application Process Status"
        # PID=`ps -fu ${USER} | grep -iw "${APP_PATH}" | grep -v grep | awk '{print $2}'`
        PID_LIST=`ps -fu ${USER} | grep -iw gunicorn | grep "${APP_NAME}" | grep -v grep | awk '{print $2}' ORS=' '`
        echo "INFO : Process Id $PID_LIST"
        PID=`ps -fu ${USER} | grep -iw gunicorn | grep "${APP_NAME}" | grep -v grep | awk '{print $2}'`
        #echo -e "INFO : Process Id $PID"
}
startApp() {
        setEnv
        getPID
        if [ "${PID}" == "" ]; then
          echo -e "INFO : Application is not running!!!"
          echo -e "INFO : Starting Application"
          cd $WEB_APP_HOME
          source $APP_VENV
          gunicorn app.main:app \
                 --workers=$APP_WORKER \
                 --worker-class=$APP_WORKER_CLASS \
                 --timeout=$APP_WORKER_TIMEOUT \
                 --bind=$APP_BIND \
                 --access-logfile $APP_ACCESS_LOG \
                 --error-logfile $APP_ERROR_LOG \
                 --log-level $APP_ERROR_LOG_LEVEL \
                 --name=$APP_NAME \
                 --forwarded-allow-ips="*" \
                 --capture-output \
                 --daemon \
                 --reload \
                 --access-logformat '%(h)s %(l)s %(asctime)s "%(r)s" %(s)s'
          sleep 3
          echo -e "INFO : Please check the logs for more Info"
        else
          echo -e "INFO : Application is running!!!";
          echo -e "INFO : Exiting Command"
          exit 0;
        fi
}
stopApp() {
        setEnv
        getPID
        if [[ "${PID}" == "" ]]; then
                echo -e "INFO : Application is not running!!!"
                exit 0;
        else
                echo -e "INFO : Application is about to be stopped!!!";
                # echo ${PID}
                kill -9 ${PID};
        fi
}

echo "INFO : Executing Command"
export USER_MODE=$1
case "${USER_MODE}" in
                stop|STOP)
                        stopApp
                ;;

                start|START)
                        startApp
                ;;

                kill|KILL)
                        stopApp
                ;;
                restart|RESTART)
                        stopApp
                        sleep 2
                        startApp
                ;;
                 -h|--help) cat <<EOH
usage: $(basename $0) [stop | start | restart | undeploy | deploy]
        STOP or stop,
                To undeploy the applications & stop the server
        START or start,
                To start the server & deploy the applications
        kill or -k,
                To kill the running process of this server
        restart or RESTART,
                To restart the running applications
        -h, --help
                Display this help and exit.
EOH
        exit 1;
                ;;
    *) echo -e "ERROR : Invalid Usage. Use --help to find more!";;
  esac
                                       